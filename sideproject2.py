import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import PyPDF2
import docx
import re
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IndonesianStemmer:
    def __init__(self):
        self.prefixes = ['meng', 'men', 'me', 'di', 'ter', 'pe', 'be', 'se']
        self.suffixes = ['ku', 'mu', 'nya', 'lah', 'kah', 'an', 'i', 'kan']

    def remove_prefix(self, word):
        for prefix in self.prefixes:
            if word.startswith(prefix):
                word = word[len(prefix):]
                break
        return word

    def remove_suffix(self, word):
        for suffix in self.suffixes:
            if word.endswith(suffix):
                word = word[:-len(suffix)]
                break
        return word

    def stem(self, word):
        word = self.remove_prefix(word)
        word = self.remove_suffix(word)
        return word

class DocumentRetrieval:
    def __init__(self):
        self.stemmer = IndonesianStemmer()
        self.stop_words = {
            'yang', 'di', 'ke', 'dari', 'pada', 'dalam', 'untuk', 'dan', 'atau', 
            'dengan', 'ini', 'itu', 'bagi', 'tentang', 'maka', 'sebab', 'serta', 
            'jika', 'karena', 'namun', 'setelah', 'kepada', 'hal', 'sudah'
        }

    def read_document(self, file_path):
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.is_encrypted:
                        try:
                            reader.decrypt('')
                        except:
                            messagebox.showwarning("Peringatan", "File PDF terenkripsi")
                            return None
                    
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text()
            elif file_ext == '.docx':
                doc = docx.Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs])
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            else:
                raise ValueError("Format file tidak didukung")
            
            return text
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca dokumen: {str(e)}")
            return None

    def custom_tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        tokens = text.split()
        return tokens

    def preprocess(self, text):
        tokens = self.custom_tokenize(text)
        
        filtered_tokens = [
            token for token in tokens 
            if token not in self.stop_words and len(token) > 1
        ]
        
        stemmed_tokens = [self.stemmer.stem(token) for token in filtered_tokens]
        
        term_weights = {}
        for token in stemmed_tokens:
            term_weights[token] = term_weights.get(token, 0) + 1
        
        return {
            'original_tokens': tokens,
            'filtered_tokens': filtered_tokens,
            'stemmed_tokens': stemmed_tokens,
            'term_weights': term_weights
        }

    def calculate_similarity(self, query, preprocessed_doc):
        query_tokens = self.custom_tokenize(query)
        query_tokens = [self.stemmer.stem(token) for token in query_tokens if token not in self.stop_words and len(token) > 1]
        
        query_freq = {}
        doc_freq = preprocessed_doc['term_weights']
        
        for token in query_tokens:
            query_freq[token] = query_freq.get(token, 0) + 1
        
        dot_product = sum(query_freq.get(token, 0) * doc_freq.get(token, 0) 
                          for token in set(query_freq) & set(doc_freq))
        
        query_magnitude = math.sqrt(sum(f**2 for f in query_freq.values()))
        doc_magnitude = math.sqrt(sum(f**2 for f in doc_freq.values()))
        
        if query_magnitude * doc_magnitude == 0:
            return 0
        
        similarity = dot_product / (query_magnitude * doc_magnitude)
        return similarity * 100

class DocumentRetrievalApp:
    def __init__(self, master):
        self.master = master
        master.title("Aplikasi Temu Balik Dokumen")
        master.geometry("1600x1000")
        master.configure(bg='#e6f2ff')

        style = ttk.Style()
        style.configure('TLabel', background='#e6f2ff', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))

        self.retrieval = DocumentRetrieval()
        
        main_frame = tk.Frame(master, bg='#e6f2ff')
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        dir_frame = tk.Frame(main_frame, bg='#e6f2ff')
        dir_frame.pack(fill=tk.X, pady=5)

        tk.Label(dir_frame, text="Pilih Direktori:", bg='#e6f2ff', font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        self.dir_button = tk.Button(dir_frame, text="Pilih Direktori", 
                                    command=self.select_directory, 
                                    bg='#4CAF50', fg='white', font=('Arial', 10))
        self.dir_button.pack(side=tk.LEFT, padx=5)

        self.file_listbox = tk.Listbox(main_frame, width=80, 
                                       bg='white', 
                                       font=('Courier', 10))
        self.file_listbox.pack(pady=10, fill=tk.X)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        query_frame = tk.Frame(main_frame, bg='#e6f2ff')
        query_frame.pack(fill=tk.X, pady=5)

        tk.Label(query_frame, text="Masukkan Query:", bg='#e6f2ff', font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        self.query_entry = tk.Entry(query_frame, width=50, font=('Arial', 10))
        self.query_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.search_button = tk.Button(query_frame, text="Cari", 
                                       command=self.search_documents, 
                                       bg='#2196F3', fg='white', font=('Arial', 10))
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.preprocessing_text = tk.Text(self.notebook, wrap=tk.WORD, 
                                          font=('Courier', 10), 
                                          bg='white')
        self.preprocessing_text.pack(fill='both', expand=True)
        self.notebook.add(self.preprocessing_text, text="Preprocessing")

        self.similarity_text = tk.Text(self.notebook, wrap=tk.WORD, 
                                       font=('Courier', 10), 
                                       bg='white')
        self.similarity_text.pack(fill='both', expand=True)
        self.notebook.add(self.similarity_text, text="Kemiripan")

        self.visualization_canvas = tk.Canvas(self.notebook, bg='#e6f2ff')
        self.visualization_scrollbar = tk.Scrollbar(self.notebook, orient="vertical", command=self.visualization_canvas.yview)
        self.visualization_frame = tk.Frame(self.visualization_canvas, bg='#e6f2ff')

        self.visualization_frame.bind("<Configure>", lambda e: self.visualization_canvas.configure(
            scrollregion=self.visualization_canvas.bbox("all")
        ))

        self.visualization_canvas.create_window((0, 0), window=self.visualization_frame, anchor="nw")
        self.visualization_canvas.configure(yscrollcommand=self.visualization_scrollbar.set)

        self.visualization_canvas.pack(side="left", fill="both", expand=True)
        self.visualization_scrollbar.pack(side="right", fill="y")
        
        self.notebook.add(self.visualization_canvas, text="Visualisasi")

    def create_pie_chart(self, data, title):
        plt.figure(figsize=(8, 6), facecolor='#e6f2ff')
        plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', 
                colors=['#2196F3', '#4CAF50', '#FF9800'])
        plt.title(title, fontsize=14)
        return plt.gcf()
    
    def create_term_weights_bar_chart(self, term_weights):
        plt.figure(figsize=(12, 6), facecolor='#e6f2ff')
        sorted_data = dict(sorted(term_weights.items(), key=lambda item: item[1], reverse=True)[:10])
        plt.bar(sorted_data.keys(), sorted_data.values(), color='#2196F3')
        plt.title('10 Token Teratas Berdasarkan Bobot (TF)', fontsize=16)
        plt.xlabel('Token', fontsize=12)
        plt.ylabel('Frekuensi', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return plt.gcf()

    def create_bar_chart(self, data, title):
        plt.figure(figsize=(10, 6), facecolor='#e6f2ff')
        sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True)[:10])
        plt.bar(sorted_data.keys(), sorted_data.values(), color='#2196F3')
        plt.title(title, fontsize=14)
        plt.xlabel('Token', fontsize=10)
        plt.ylabel('Frekuensi', fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return plt.gcf()

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.file_listbox.delete(0, tk.END)
            supported_ext = ['.pdf', '.docx', '.txt']
            for filename in os.listdir(directory):
                if any(filename.lower().endswith(ext) for ext in supported_ext):
                    self.file_listbox.insert(tk.END, os.path.join(directory, filename))

    def create_term_weights_bar_charts(self, term_weights):
        plt.figure(figsize=(12, 8), facecolor='#e6f2ff')
        plt.subplot(2, 1, 1)
        sorted_term_weights = dict(sorted(term_weights.items(), key=lambda x: x[1], reverse=True)[:10])
        plt.bar(sorted_term_weights.keys(), sorted_term_weights.values(), color='#2196F3')
        plt.title('10 Token Teratas Berdasarkan Bobot (TF)', fontsize=12)
        plt.xlabel('Token', fontsize=10)
        plt.ylabel('Frekuensi', fontsize=10)
        plt.xticks(rotation=45, ha='right')

        plt.subplot(2, 1, 2)
        log_term_weights = {k: math.log1p(v) for k, v in sorted_term_weights.items()}
        plt.bar(log_term_weights.keys(), log_term_weights.values(), color='#4CAF50')
        plt.title('Log Transformasi Bobot Token', fontsize=12)
        plt.xlabel('Token', fontsize=10)
        plt.ylabel('Log(Frekuensi + 1)', fontsize=10)
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        return plt.gcf()
    
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            file_path = self.file_listbox.get(selection[0])
            document = self.retrieval.read_document(file_path)
            
            if document:
                preprocessed = self.retrieval.preprocess(document)
                
                self.preprocessing_text.delete('1.0', tk.END)
                self.preprocessing_text.tag_configure('header', font=('Arial', 12, 'bold'), foreground='navy')
                
                self.preprocessing_text.insert(tk.END, "📋 Original Tokens\n", 'header')
                self.preprocessing_text.insert(tk.END, f"Total: {len(preprocessed['original_tokens'])}\n")
                self.preprocessing_text.insert(tk.END, str(preprocessed['original_tokens']) + "\n\n")
                
                self.preprocessing_text.insert(tk.END, "🧹 Filtered Tokens (Stop Word Removal)\n", 'header')
                self.preprocessing_text.insert(tk.END, f"Total: {len(preprocessed['filtered_tokens'])}\n")
                self.preprocessing_text.insert(tk.END, str(preprocessed['filtered_tokens']) + "\n\n")
                
                self.preprocessing_text.insert(tk.END, "🌱 Stemmed Tokens\n", 'header')
                self.preprocessing_text.insert(tk.END, f"Total: {len(preprocessed['stemmed_tokens'])}\n")
                self.preprocessing_text.insert(tk.END, str(preprocessed['stemmed_tokens']) + "\n\n")
                
                self.preprocessing_text.insert(tk.END, "⚖️ Term Weights (TF)\n", 'header')
                for token, weight in preprocessed['term_weights'].items():
                    self.preprocessing_text.insert(tk.END, f"{token}: {weight}\n")

                for widget in self.visualization_frame.winfo_children():
                    widget.destroy()

                token_types = {
                    'Original Tokens': len(preprocessed['original_tokens']),
                    'Filtered Tokens': len(preprocessed['filtered_tokens']),
                    'Stemmed Tokens': len(preprocessed['stemmed_tokens'])
                }
                pie_fig = self.create_pie_chart(token_types, 'Distribusi Tipe Token')
                pie_canvas = FigureCanvasTkAgg(pie_fig, master=self.visualization_frame)
                pie_canvas.draw()
                pie_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                top_10_weights = dict(list(sorted(preprocessed['term_weights'].items(), key=lambda x: x[1], reverse=True))[:10])
                bar_fig = self.create_term_weights_bar_chart(top_10_weights)
                bar_canvas = FigureCanvasTkAgg(bar_fig, master=self.visualization_frame)
                bar_canvas.draw()
                bar_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def search_documents(self):
        query = self.query_entry.get()
        if not query:
            messagebox.showwarning("Peringatan", "Masukkan query terlebih dahulu")
            return

        self.similarity_text.delete('1.0', tk.END)
        self.similarity_text.tag_configure('header', font=('Arial', 12, 'bold'), foreground='navy')

        for i in range(self.file_listbox.size()):
            file_path = self.file_listbox.get(i)
            document = self.retrieval.read_document(file_path)
            
            if document:
                preprocessed = self.retrieval.preprocess(document)
                similarity = self.retrieval.calculate_similarity(query, preprocessed)
                
                self.similarity_text.insert(tk.END, "📄 File: ", 'header')
                self.similarity_text.insert(tk.END, f"{os.path.basename(file_path)}\n")
                self.similarity_text.insert(tk.END, f"🔍 Tingkat Kemiripan: {similarity:.2f}%\n\n")
def main():
    root = tk.Tk()
    app = DocumentRetrievalApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()