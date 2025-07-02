from langchain_community.document_loaders import WebBaseLoader
import bs4

def get_webpage_content(url):
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(parse_only=bs4.SoupStrainer(class_=("firstHeading mw-first-heading","mw-body-content")))
    )
    text_documents = loader.load()
    return text_documents

def process_documents(text_documents):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.split_documents(text_documents)
    return documents
