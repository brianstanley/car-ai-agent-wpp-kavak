import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from utils.tokenizer import OpenAITokenizerWrapper
from services.kavak_info_service import KavakInfoService

# Load environment variables
load_dotenv()

def main():
    """Extract Kavak information and store it in the database."""

    # Initialize services and utilities
    tokenizer = OpenAITokenizerWrapper()
    kavak_service = KavakInfoService()
    MAX_TOKENS = 8191  # text-embedding-3-small's maximum context length

    print("Starting Kavak information extraction...")

    # Initialize document converter
    converter = DocumentConverter()

    # Convert the Kavak website
    print("Converting Kavak website...")
    result = converter.convert("https://www.kavak.com/mx/blog/sedes-de-kavak-en-mexico")

    # Initialize chunker with correct parameters
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,
    )

    # Chunk the document
    print("Chunking document...")
    chunk_iter = chunker.chunk(dl_doc=result.document)
    chunks = list(chunk_iter)

    print(f"Created {len(chunks)} chunks")

    # Process and store chunks in database
    print("Processing chunks and storing in database...")
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        title = chunk.meta.headings[-1] if getattr(chunk.meta, "headings", None) else None
        metadata = chunk.meta.metadata if getattr(chunk.meta, "metadata", None) else None
        if metadata and hasattr(metadata[0], "dict"):
                metadata = [item.dict() for item in metadata]
        elif metadata and hasattr(metadata[0], "__str__"):
            metadata = [str(item) for item in metadata]

        try:
            success = kavak_service.create_kavak_info_with_embedding(
                text=chunk.text,
                title=title,
                metadata=metadata

            )
            if success:
                print(f"  ✓ Stored chunk {i+1} with {len(tokenizer.tokenize(chunk.text))} tokens")
            else:
                print(f"  ✗ Failed to store chunk {i+1}")
        except Exception as e:
            print(f"  ✗ Error storing chunk {i+1}: {e}")

    print("Extraction complete!")

    # Display summary
    all_records = kavak_service.get_all_kavak_info()
    print(f"Total records in database: {len(all_records)}")

if __name__ == "__main__":
    main()