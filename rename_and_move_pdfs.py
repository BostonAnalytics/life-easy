import os
import re
import shutil
import fitz  # PyMuPDF
from tqdm import tqdm  # For progress bar

# Define source and destination folders (Your paths)
source_folder = "E:/Downloads"
destination_folder = "E:/KnowledgeBase-Papers"

# Create destination folder if it doesn't exist
os.makedirs(destination_folder, exist_ok=True)

def extract_metadata(pdf_path):
    """Extract first author, year, title, DOI, or ArXiv ID from the first page of a PDF"""
    try:
        with fitz.open(pdf_path) as doc:
            first_page = doc[0].get_text("text")  # Extract text from first page
            
            # Extract first author (assuming format "Author, First")
            author_match = re.search(r"(?P<author>[A-Z][a-z]+),", first_page)
            author = author_match.group("author") if author_match else "Unknown"

            # Extract year (assuming 4-digit year appears)
            year_match = re.search(r"\b(20\d{2})\b", first_page)  # Matches 2020-2029
            year = year_match.group(1) if year_match else "YYYY"

            # Extract title (assuming title is capitalized and appears early)
            title_lines = first_page.split("\n")
            title = "Untitled"
            for line in title_lines:
                words = line.strip().split()
                if 5 <= len(words) <= 12:  # Title should be between 5-12 words
                    title = " ".join(words[:4])  # Take the first 4 words
                    break

            # Extract DOI (Elsevier) or ArXiv ID
            doi_match = re.search(r"10\.\d{4,9}/[^\s]+", first_page)  # DOI pattern
            arxiv_match = re.search(r"arXiv:(\d{4}\.\d{4,5})", first_page)  # ArXiv ID pattern
            identifier = doi_match.group(0) if doi_match else (arxiv_match.group(1) if arxiv_match else "")

            return author, year, title.replace(" ", "_"), identifier
    
    except Exception as e:
        print(f"Skipping {os.path.basename(pdf_path)} due to error: {e}")
        return None  # Return None to indicate an error

def rename_and_move_pdfs():
    # Get the list of valid PDF files (Only matching ArXiv or Elsevier patterns)
    pdf_files = [
        f for f in os.listdir(source_folder)
        if f.endswith(".pdf") and (
            re.match(r"\d{4}\.\d{5,7}v\d", f) or  # Matches ArXiv format (e.g., 2412.17686v1.pdf)
            f.startswith("1-s2.0-")  # Matches Elsevier format (e.g., 1-s2.0-S2666544124000212-main.pdf)
        )
    ]

    if not pdf_files:
        print("No valid ArXiv or Elsevier PDFs found in the source folder.")
        return

    # Ask the user how many files to process
    while True:
        try:
            num_files = int(input(f"Enter the number of PDFs to process (max {len(pdf_files)}): "))
            if num_files <= 0:
                print("Please enter a positive number.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    # Limit the number of files to process
    pdf_files = pdf_files[:min(num_files, len(pdf_files))]

    # Using tqdm for a progress bar
    for filename in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
        file_path = os.path.join(source_folder, filename)
        
        # Extract metadata
        metadata = extract_metadata(file_path)
        if metadata is None:
            continue  # Skip the file if metadata extraction failed

        author, year, title, identifier = metadata

        # Determine source label
        if filename.startswith("1-s2.0-"):
            label = "elsevier"
        elif re.match(r"\d{4}\.\d{5,7}v\d", filename):
            label = "arxiv"
        else:
            label = "unknown"

        # Construct new filename with DOI or ArXiv ID if available
        if identifier:
            new_filename = f"{author}({year})-{title}-{label}-{identifier}.pdf"
        else:
            new_filename = f"{author}({year})-{title}-{label}.pdf"

        new_file_path = os.path.join(destination_folder, new_filename)
        
        try:
            # Move the file to the destination folder
            shutil.move(file_path, new_file_path)
        except Exception as e:
            print(f"Skipping {filename} due to file move error: {e}")

    print(f"\nSuccessfully processed {len(pdf_files)} PDF(s), skipping any files with errors.")

# Run the script
rename_and_move_pdfs()
