file_path = "data\17-nachhaltigkeitsziele-in-berlin.pdf"

import pdfplumber
import re
from PyPDF2 import PdfReader, PdfWriter
import os

#Funktion um die Einträge im Inhalt(sverzeichnis zu finden)
def extract_text_from_pdf(file_path):
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Hier kann man nach dem Inhaltsverzeichnis suchen
            if "Inhalt" in text:
                return text.split("Inhalt")[1]
    return None

text = extract_text_from_pdf(file_path)
#print(text) entkommentieren, falls man den output testen will

#Extrahieren der Abschnittsnamen im Inhaltsverzeichnis
# Regex für den ersten Abschnitt
first_pattern = r"^(?:(1(?:\.\d+)*\.?|AP 1(?:\.\d+)*\.?|AP 0\.?)(?:[.:]?)\s+([^\.\n]+))"

# Regex für alle weiteren Abschnitte
subsequent_pattern = r"^(?:(\d+\.\d*|AP \d+\.\d*|AP \d+:[.:]?|\d+)[.:]?)\s+([^\.\n]+)"

# Suche nach dem ersten Abschnitt
first_match = re.search(first_pattern, text, re.MULTILINE)

# Wenn der erste Match gefunden wurde, verarbeite die restlichen
if first_match:
    abschnitte = [f"{first_match.group(1).strip()} {first_match.group(2).strip()}"]
    
    # Schneide den Text ab dem ersten Match ab und suche nach den weiteren Abschnitten
    remaining_text = text[first_match.end():]
    subsequent_matches = re.findall(subsequent_pattern, remaining_text, re.MULTILINE)
    
    # Füge die restlichen Abschnitte hinzu
    abschnitte.extend([f"{num.strip()} {name.strip()}" for num, name in subsequent_matches])
else:
    abschnitte = []  # Falls kein gültiger erster Abschnitt gefunden wird

#print(abschnitte) entkommentieren falls man testen will was gefunden wurde

###PDF Aufräumen und Abschnitte extrahieren###

#Funktion um alles bis nach dem Innhaltsverzeichnis aus der pdf datei zu löschen, damit Inhaltsverzeichnis nicht erneut extrahiert wird
def remove_pages_before_contents(pdf_path, output_path, contents_start_page=1):
    """
    Remove pages before the content starts (after the table of contents).
    
    :param pdf_path: Path to the original PDF file.
    :param output_path: Path to save the new PDF file without the first pages.
    :param contents_start_page: The page number (0-indexed) where the content starts.
    :return: None
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Add pages starting from the contents_start_page to the new PDF
    for page_num in range(contents_start_page, len(reader.pages)):
        writer.add_page(reader.pages[page_num])

    # Write the new PDF to the output path
    with open(output_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"New PDF saved to: {output_path}")

#Funktion um die einzelnen Abschnitte zu finden und zu extrahieren
def extract_sections_from_pdf(pdf_path, sections):
    """
    Extract specified sections from a PDF file, starting at the match's start.

    :param pdf_path: Path to the PDF file.
    :param sections: List of section headings to extract.
    :return: Dictionary with section headings as keys and extracted text as values.
    """
    # Read the PDF
    reader = PdfReader(pdf_path)
    text = ""

    # Combine text from all pages
    for page in reader.pages:
        text += page.extract_text()

    # Prepare a regex pattern to match sections
    sections_pattern = [re.escape(sec).replace(r'\ ', r'\s+') for sec in sections]
    regex = re.compile(f"({'|'.join(sections_pattern)})", re.MULTILINE)


    # Find matches and extract content
    matches = list(regex.finditer(text))
    extracted_sections = {}


    # Loop through the matches to extract text for each section
    for i, match in enumerate(matches):
        start = match.start()  # Start from the beginning of the match

        # Define the end position as the start of the next section or the end of the text
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        # Extract the text for this section
        section_text = text[start:end].strip()

        # Store the extracted section text
        extracted_sections[match.group()] = section_text

    return extracted_sections

pdf_path = file_path
new_pdf_path = "data/cleaned_pdf.pdf"  # New PDF after removing pages up to the contents
sections = abschnitte  # Liste der Abschnitte, die du extrahieren möchtest

# Call Funktion to remove pages before the table of contents
remove_pages_before_contents(pdf_path, new_pdf_path, contents_start_page=2)  # Page 1 is the second page - Aktuell noch manuell die passende Seite eingegeben

# Extract sections from the cleaned PDF
extracted_sections = extract_sections_from_pdf(new_pdf_path, abschnitte)

# Entkommentieren um zu sehen was extrahiert wurde
#for section, content in extracted_sections.items():
#    print(f"Section: {section}\nContent:\n{content}\n{'-'*40}\n")

#Funktion um die extrahierten abschnitte in textdateien zu speichern
def save_sections_as_text_files(extracted_sections, output_directory):
    """
    Saves each section as a separate text file in the specified directory.
    
    :param extracted_sections: Dictionary with section names as keys and content as values.
    :param output_directory: Directory where the text files will be saved.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for section, content in extracted_sections.items():
        # Sanitize the section name to make it a valid filename
        filename = re.sub(r'[\\/*?:"<>|]', "_", section)  # Replace invalid characters with underscores
        file_path = os.path.join(output_directory, f"{filename}.txt")

        # Write the content into the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Section '{section}' saved to '{file_path}'")


output_directory = "extracted_sections"  # Directory to save the text files

# Funktions aufrufen, um die Abschnitte in Textdateien zu speichern
save_sections_as_text_files(extracted_sections, output_directory)
