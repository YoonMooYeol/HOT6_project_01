from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from langchain_community.document_loaders import DirectoryLoader, JSONLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
import chromadb
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from dotenv import load_dotenv
import os
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from openai import RateLimitError, APIError
from langchain_core.prompts import ChatPromptTemplate
import re
from .models import JsonFile, Message
from .serializers import MessageSerializer

load_dotenv()

class RagSetupViewSet(APIView):
    BATCH_SIZE = 500

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.processed_utterances = self.load_existing_utterances()

    def is_file_processed(self, file_path):
        """파일이 이미 처리되었는지 확인"""
        return JsonFile.objects.filter(file_path=file_path).exists()

    def mark_file_as_processed(self, file_path):
        """파일을 처리됨으로 표시"""
        JsonFile.objects.create(file_path=file_path)

    def filter_metadata(self, metadata):
        """None 값을 문자열로 변환하고 복잡한 메타데이터 필터링"""
        filtered = {}
        for key, value in metadata.items():
            if value is None:
                filtered[key] = "none"  # None을 문자열로 변환
            elif isinstance(value, (str, int, float, bool)):
                filtered[key] = value
        return filtered

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),  # 대기 시간도 조정
        before_sleep=lambda retry_state: print(f"⏳ {retry_state.attempt_number}번째 재시도... {retry_state.outcome.exception()} 발생")
    )
    def process_batch(self, docs, vector_store=None, embeddings=None, persist_dir=None):
        try:
            # 배치 크기 로깅 추가
            total_tokens = sum(len(doc.page_content.split()) for doc in docs)
            print(f"📦 현재 배치: {len(docs)}개 문서, 약 {total_tokens}개 토큰")
            
            # 각 문서의 메타데이터 필터링
            for doc in docs:
                doc.metadata = self.filter_metadata(doc.metadata)

            if vector_store is None:
                vector_store = Chroma(
                    client=self.client,
                    collection_name="persona_chat",
                    embedding_function=embeddings
                )
            
            vector_store.add_documents(docs)
            return vector_store
            
        except Exception as e:
            print(f"🚨 배치 처리 중 에러 발생: {str(e)}")
            raise

    def load_single_json(self, file_path):
        """단일 JSON 파일 로드 및 처리"""
        try:
            loader = JSONLoader(
                file_path=file_path,
                jq_schema=".utterances[]",
                content_key="text",
                metadata_func=lambda metadata, content: {
                    "persona_id": str(content.get("persona_id", "")),  # None 방지를 위해 기본값 설정
                    "utterance_id": str(content.get("utterance_id", "")),
                    "terminate": bool(content.get("terminate", False)),
                    "category": str(metadata.get("info", {}).get("category", "")),
                    "topic": str(metadata.get("info", {}).get("topic", "")),
                    "file_id": str(metadata.get("info", {}).get("id", "")),
                    "file_name": str(metadata.get("info", {}).get("name", "")),
                    "source_file": str(file_path)
                }
            )
            docs = loader.load()
            print(f"✅ 성공: {file_path} - {len(docs)}개 문서 로드")
            return docs
        except Exception as e:
            print(f"❌ 실패: {file_path} - 에러: {str(e)}")
            return []

    def load_existing_utterances(self):
        """기존 벡터 DB에서 utterance_id 목록 로드"""
        try:
            collection = self.client.get_collection("persona_chat")
            existing_metadata = collection.get()["metadatas"]
            return {meta["utterance_id"] for meta in existing_metadata if meta and "utterance_id" in meta}
        except:
            return set()

    def filter_new_docs(self, docs):
        """새로운 문서만 필터링"""
        new_docs = []
        for doc in docs:
            utterance_id = doc.metadata.get("utterance_id")
            if utterance_id and utterance_id not in self.processed_utterances:
                self.processed_utterances.add(utterance_id)
                new_docs.append(doc)
        return new_docs

    def post(self, request):
        try:
            data_dir = "data"
            if not os.path.exists(data_dir):
                return Response(
                    {"error": "data 디렉토리가 존재하지 않습니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            embeddings = OpenAIEmbeddings()
            
            try:
                vector_store = Chroma(
                    client=self.client,
                    collection_name="persona_chat",
                    embedding_function=embeddings
                )
                print("📚 기존 벡터 스토어를 로드했습니다.")
            except:
                vector_store = None
                print("🆕 새로운 벡터 스토어를 생성합니다.")

            # JSON 파일들을 개별적으로 처리
            all_docs = []
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            print("\n🔍 JSON 파일 처리 시작...")
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        
                        # 이미 처리된 파일인지 확인
                        if self.is_file_processed(file_path):
                            print(f"⏩ 건너뜀: {file_path} - 이미 처리된 파일")
                            skipped_count += 1
                            continue

                        docs = self.load_single_json(file_path)
                        if docs:
                            all_docs.extend(docs)
                            success_count += 1
                            self.mark_file_as_processed(file_path)
                        else:
                            error_count += 1

            if not all_docs:
                print("\n⚠️ 처리할 새로운 문서가 없습니다.")
                return Response({
                    "message": "추가할 새로운 문서가 없습니다.",
                    "skipped_documents": skipped_count,
                    "existing_documents": len(self.processed_utterances)
                })

            print(f"\n📊 처리 통계:")
            print(f"- 성공: {success_count} 파일")
            print(f"- 실패: {error_count} 파일")
            print(f"- 건너뜀: {skipped_count} 문서")
            print(f"- 새로운 문서 수: {len(all_docs)}개")

            # 배치 처리
            total_processed = 0
            failed_batches = []
            print("\n💫 임베딩 처리 시작...")
            
            for i in range(0, len(all_docs), self.BATCH_SIZE):
                batch = all_docs[i:i + self.BATCH_SIZE]
                batch_start = i
                batch_end = min(i + self.BATCH_SIZE, len(all_docs))
                
                try:
                    print(f"\n🔄 배치 처리 중... ({batch_start+1}-{batch_end}/{len(all_docs)})")
                    vector_store = self.process_batch(
                        batch, 
                        vector_store, 
                        embeddings
                    )
                    total_processed += len(batch)
                    print(f"✅ 진행률: {total_processed}/{len(all_docs)} 문서 처리됨")
                    
                    if vector_store:
                        print("💾 데이터가 자동으로 저장되었습니다.")
                
                except Exception as batch_error:
                    print(f"❌ 배치 처리 실패 ({batch_start+1}-{batch_end}): {str(batch_error)}")
                    failed_batches.append((batch_start, batch_end))
                    continue

            if failed_batches:
                print("\n⚠️ 실패한 배치 목록:")
                for start, end in failed_batches:
                    print(f"- {start+1}-{end} 범위의 문서")

            print(f"\n✨ 작업 완료!")
            return Response({
                "message": "벡터 스토어가 업데이트되었습니다.",
                "new_documents_count": total_processed,
                "skipped_documents": skipped_count,
                "existing_documents": len(self.processed_utterances),
                "success_files": success_count,
                "error_files": error_count,
                "failed_batches": failed_batches
            })
            
        except Exception as e:
            print(f"\n🚨 치명적 오류: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class RagChatViewSet(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 벡터 스토어 초기화
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(
            client=chromadb.PersistentClient(path="./chroma_db"),
            collection_name="persona_chat",
            embedding_function=self.embeddings
        )
        self.retriever = self.vector_store.as_retriever()
        
        # LLM 및 프롬프트 설정 (deprecated 경고 수정)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  
            temperature=0.7
        )
        self.prompt = ChatPromptTemplate.from_template(
            """
            1. When responding to my messages, maintain a gentle and non-confrontational tone, as if I am speaking directly. 
               Rephrase my words in a warm and considerate manner to convey emotions and concerns respectfully. 
               Keep responses concise and focused on delivering my intended message.
            2. (Most Important) I am not talking to an AI; I am conversing with my partner. 
               Translate my words into a response of 10 characters or fewer that aligns with the specified tone.
            3. Speak in the following manner: gentle, warm, and considerate.
            4. always speak korean
            5. provide 3 examples of messages that can be used to respond to the user's message
            Question: {question}
            Context: {context}

            Read the user's message and rephrase it according to the specified style in the following format:  
            Response format: "User's message" : "Rephrased message1, Rephrased message2, Rephrased message3"
            
            """
        )

    def post(self, request):
        try:
            # 입력 메시지와 유저 ID 확인
            message = request.data.get('message')
            user_id = request.data.get('user_id')
            
            if not message:
                return Response(
                    {"error": "메시지를 입력해주세요."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not user_id:
                return Response(
                    {"error": "유저 ID를 입력해주세요."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 벡터 DB가 비어있는지 확인
            if not self.vector_store._collection.count():
                return Response(
                    {"error": "벡터 DB에 데이터가 없습니다. 먼저 데이터를 임베딩해주세요."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 관련 문서 검색
            docs = self.retriever.invoke(message)
            context = "\n".join([doc.page_content for doc in docs])

            # RAG 실행
            chain = self.prompt | self.llm
            response = chain.invoke({
                "context": context,
                "question": message
            })

            # 답변 추출
            try:
                # 콜론 이후의 모든 따옴표 내용을 추출
                match = re.search(r':\s*"(.+?)(?:")?$', response.content, re.DOTALL)
                if match:
                    # 모든 따옴표를 제거하고 저장
                    translated_message = match.group(1).replace('"', '').strip()
                else:
                    translated_message = response.content.replace('"', '').strip()
            except:
                translated_message = response.content.replace('"', '').strip()

            # 결과를 데이터베이스에 저장
            message_obj = Message.objects.create(
                user_id=user_id,
                input_content=message,
                output_content=response.content,
                translated_content=translated_message
            )

            return Response({
                "message_id": message_obj.id,  # BigAutoField ID 반환
                "user_id": message_obj.user_id,
                "original_message": message_obj.input_content,
                "translated_message": message_obj.translated_content,
                "full_response": message_obj.output_content,
                "created_at": message_obj.created_at
            }, status=status.HTTP_201_CREATED)  # 201 Created 상태 코드 사용

        except Exception as e:
            print(f"🚨 Error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        return Response({
            "user_id": 1,
            "message": "채팅 API입니다. POST 요청을 통해 메시지를 전송해주세요. 더러운 메시지를 처리합니다."
        })
            
class RagSyncViewSet(APIView):
    """크로마 DB와 SQLite DB 동기화를 위한 ViewSet"""
    
    def post(self, request):
        try:
            # 크로마 DB 연결
            client = chromadb.PersistentClient(path="./chroma_db")
            try:
                collection = client.get_collection("")
                metadata_list = collection.get()["metadatas"]
                print(f"📚 크로마 DB에서 {len(metadata_list)}개의 문서 메타데이터를 불러왔습니다.")
            except Exception as e:
                return Response({
                    "error": "크로마 DB에서 데이터를 불러올 수 없습니다.",
                    "detail": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            # 고유한 파일 경로 추출
            processed_files = set()
            for metadata in metadata_list:
                if metadata and "source_file" in metadata:
                    processed_files.add(metadata["source_file"])

            # 현재 SQLite DB에 저장된 파일 목록
            existing_files = set(JsonFile.objects.values_list('file_path', flat=True))

            # 새로 추가할 파일들
            new_files = processed_files - existing_files

            # SQLite DB에 새 파일들 추가
            for file_path in new_files:
                JsonFile.objects.create(file_path=file_path)

            return Response({
                "message": "크로마 DB와 SQLite DB가 동기화되었습니다.",
                "total_files_in_chroma": len(processed_files),
                "existing_files_in_sqlite": len(existing_files),
                "newly_added_files": len(new_files),
                "new_files": list(new_files)
            })

        except Exception as e:
            print(f"🚨 동기화 중 오류 발생: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
