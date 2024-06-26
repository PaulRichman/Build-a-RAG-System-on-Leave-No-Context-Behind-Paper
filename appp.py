import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import NLTKTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader


st.title("RAG on Leave No Context Behind Paper")
st.sidebar.header("Options")
user_input = st.text_input("Enter your question...")

chat_model = ChatGoogleGenerativeAI(google_api_key="AIzaSyC2Bztff9XtDCDrCJfMJ8py9JaT8VkwSlY", 
                                    model="gemini-1.5-pro-latest")

chat_template = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are a Helpful AI Bot. 
    You take the question from the user and answer if you have specific information related to the question."""),
    HumanMessagePromptTemplate.from_template("""Answer the following question: {question}
    Answer: """)
])

output_parser = StrOutputParser()

loader = PyPDFLoader(r"2404.07143.pdf")
data = loader.load()

text_splitter = NLTKTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(data)

embedding_model = GoogleGenerativeAIEmbeddings(google_api_key="AIzaSyC2Bztff9XtDCDrCJfMJ8py9JaT8VkwSlY", 
                                               model="models/embedding-001")

db = Chroma.from_documents(chunks, embedding_model, persist_directory="./chroma_db_")
db.persist()

db_connection = Chroma(persist_directory="./chroma_db_", embedding_function=embedding_model)
retriever = db_connection.as_retriever(search_kwargs={"k": 5})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chat_template = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are a Helpful AI Bot. 
    You take the context and question from the user. Your answer should be based on the specific context."""),
    HumanMessagePromptTemplate.from_template("""Answer the question based on the given context.
    Context:
    {context}
    
    Question: 
    {question}
    
    Answer: """)
])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | chat_template
    | chat_model
    | output_parser
)

if st.sidebar.button("Generate Answer"):
    response = rag_chain.invoke(user_input)
    st.write(response)
    
