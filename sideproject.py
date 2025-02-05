import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from PyPDF2 import PdfReader
from docx import Document
from collections import Counter

# [Previous helper functions remain the same until the GUI part]
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def list_files(directory):
    return [f for f in os.listdir(directory) if f.endswith((".pdf", ".docx", ".txt"))]

def load_stopwords(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return set(file.read().split())
    else:
        messagebox.showerror(
            "Error",
            f"File '{file_path}' tidak ditemukan. Menggunakan stopwords kosong.",
        )
        return set()

def preprocess(text, stopwords, use_stopwords=True):
    text = text.lower()
    tokens = re.findall(r"\b\w+\b", text)
    if use_stopwords:
        tokens = [word for word in tokens if word not in stopwords]
    stemmer = StemmerFactory().create_stemmer()
    stemmed = [stemmer.stem(word) for word in tokens]
    return stemmed

def calculate_similarity(documents, query):
    vectorizer = TfidfVectorizer()
    all_documents = documents + [query]
    tfidf_matrix = vectorizer.fit_transform(all_documents)
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    return cosine_sim.flatten()

def run_search_gui():
    def browse_directory():
        directory = filedialog.askdirectory()
        if directory:
            entry_directory.delete(0, tk.END)
            entry_directory.insert(0, directory)
            load_files(directory)

    def load_files(directory):
        files = list_files(directory)
        listbox_files.delete(0, tk.END)
        for file in files:
            listbox_files.insert(tk.END, file)
        listbox_files.selection_clear(0, tk.END)

    def on_search():
        directory = entry_directory.get()
        stopwords_path = "E:\Semester 5\DATMIN\side\stopwords.txt"
        stopwords = load_stopwords(stopwords_path)

        selected_file_index = listbox_files.curselection()
        if not selected_file_index:
            messagebox.showwarning("Warning", "Pilih file terlebih dahulu.")
            return

        selected_file = listbox_files.get(selected_file_index[0])
        file_path = os.path.join(directory, selected_file)

        try:
            if file_path.endswith(".pdf"):
                content = read_pdf(file_path)
            elif file_path.endswith(".docx"):
                content = read_docx(file_path)
            elif file_path.endswith(".txt"):
                content = read_txt(file_path)
            else:
                messagebox.showwarning("Warning", "Format file tidak didukung.")
                return

            processed_content = preprocess(content, stopwords, use_stopwords=True)
            word_counts = Counter(processed_content)
            total_words = sum(word_counts.values())

            # Clear and update output with custom tags
            text_output.delete(1.0, tk.END)
            text_output.tag_configure("header", font=("Helvetica", 11, "bold"), foreground="#2D3436")
            text_output.tag_configure("content", font=("Helvetica", 10), foreground="#2D3436")
            text_output.tag_configure("highlight", background="#F0F0F0")

            text_output.insert(tk.END, "Konten Asli:\n", "header")
            text_output.insert(tk.END, f"{content}\n\n", "content")
            text_output.insert(tk.END, "Konten Setelah Preprocessing:\n", "header")
            text_output.insert(tk.END, f"{' '.join(processed_content)}\n\n", "content")
            text_output.insert(tk.END, "Kata Dasar dan Frekuensinya:\n", "header")
            
            for word, count in word_counts.items():
                text_output.insert(tk.END, f"{word}: {count}\n", "content")
            
            text_output.insert(tk.END, f"\nTotal Kata Dasar: {total_words}\n\n", "highlight")

            query = entry_query.get()
            if not query:
                messagebox.showwarning("Warning", "Masukkan query pencarian.")
                return

            query_processed = preprocess(query, stopwords, use_stopwords=True)
            all_documents = [" ".join(processed_content)]
            similarities = calculate_similarity(all_documents, " ".join(query_processed))

            text_output.insert(tk.END, "Skor Kemiripan:\n", "header")
            for idx, score in enumerate(similarities):
                text_output.insert(tk.END, f"{selected_file}: {score:.4f}\n", "highlight")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")

    # Window setup
    window = tk.Tk()
    window.title("Document Search System")
    window.configure(bg="#FFFFFF")
    window.geometry("800x800")  # Set fixed window size

    # Style constants
    COLORS = {
        'primary': '#2D3436',    # Dark gray
        'secondary': '#636E72',  # Medium gray
        'accent': '#00B894',     # Mint green
        'background': '#FFFFFF', # White
        'surface': '#F5F6FA'     # Light gray
    }

    # Header frame
    header_frame = tk.Frame(window, bg=COLORS['primary'], pady=15)
    header_frame.pack(fill=tk.X)

    title_label = tk.Label(
        header_frame, 
        text="SISTEM PENCARIAN DOKUMEN", 
        font=("Helvetica", 18, "bold"),
        bg=COLORS['primary'],
        fg=COLORS['background']
    )
    title_label.pack()

    # Main content frame
    main_frame = tk.Frame(window, bg=COLORS['background'], pady=20, padx=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Directory selection frame
    dir_frame = tk.Frame(main_frame, bg=COLORS['background'])
    dir_frame.pack(fill=tk.X, pady=(0, 10))

    label_directory = tk.Label(
        dir_frame,
        text="Direktori:",
        font=("Helvetica", 10, "bold"),
        bg=COLORS['background'],
        fg=COLORS['primary']
    )
    label_directory.pack(side=tk.LEFT, padx=(0, 10))

    entry_directory = tk.Entry(
        dir_frame,
        font=("Helvetica", 10),
        bg=COLORS['surface'],
        relief="flat",
        width=50
    )
    entry_directory.pack(side=tk.LEFT, padx=(0, 10))

    button_browse = tk.Button(
        dir_frame,
        text="Browse",
        font=("Helvetica", 10),
        bg=COLORS['accent'],
        fg=COLORS['background'],
        relief="flat",
        padx=15,
        command=browse_directory
    )
    button_browse.pack(side=tk.LEFT)

    # Query frame
    query_frame = tk.Frame(main_frame, bg=COLORS['background'])
    query_frame.pack(fill=tk.X, pady=(0, 10))

    label_query = tk.Label(
        query_frame,
        text="Query:",
        font=("Helvetica", 10, "bold"),
        bg=COLORS['background'],
        fg=COLORS['primary']
    )
    label_query.pack(side=tk.LEFT, padx=(0, 10))

    entry_query = tk.Entry(
        query_frame,
        font=("Helvetica", 10),
        bg=COLORS['surface'],
        relief="flat",
        width=50
    )
    entry_query.pack(side=tk.LEFT, padx=(0, 10))

    button_search = tk.Button(
        query_frame,
        text="Cari",
        font=("Helvetica", 10),
        bg=COLORS['accent'],
        fg=COLORS['background'],
        relief="flat",
        padx=20,
        command=on_search
    )
    button_search.pack(side=tk.LEFT)

    # Files list frame
    files_frame = tk.Frame(main_frame, bg=COLORS['background'])
    files_frame.pack(fill=tk.X, pady=(0, 10))

    label_files = tk.Label(
        files_frame,
        text="Daftar File:",
        font=("Helvetica", 10, "bold"),
        bg=COLORS['background'],
        fg=COLORS['primary']
    )
    label_files.pack(anchor="w")

    listbox_files = tk.Listbox(
        files_frame,
        font=("Helvetica", 10),
        bg=COLORS['surface'],
        relief="flat",
        height=8,
        selectmode=tk.SINGLE
    )
    listbox_files.pack(fill=tk.X, pady=(5, 0))

    # Output frame
    output_frame = tk.Frame(main_frame, bg=COLORS['background'])
    output_frame.pack(fill=tk.BOTH, expand=True)

    label_output = tk.Label(
        output_frame,
        text="Hasil Analisis:",
        font=("Helvetica", 10, "bold"),
        bg=COLORS['background'],
        fg=COLORS['primary']
    )
    label_output.pack(anchor="w")

    text_output = scrolledtext.ScrolledText(
        output_frame,
        font=("Helvetica", 10),
        bg=COLORS['surface'],
        relief="flat",
        height=20
    )
    text_output.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    window.mainloop()

if __name__ == "__main__":
    run_search_gui()