import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import random
import pyttsx3

class ChutanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chutan Knock")
        self.root.geometry("500x600")
        self.root.configure(bg="#f9f3f9")

        self.df = pd.read_excel("Chutan.xlsx", engine="openpyxl")

        self.score = 0
        self.q_num = 0
        self.total_q = 10

        self.grade_var = tk.StringVar()
        self.pos_var = tk.StringVar()

        self.setup_start_screen()

    def setup_start_screen(self):
        tk.Label(self.root, text="Chutan Knock", font=("Helvetica", 24, "bold"), bg="#f9f3f9", fg="#cc6699").pack(pady=20)

        grades = ["全学年", "中１のみ", "中２のみ", "中３のみ", "中１～２"]
        tk.Label(self.root, text="学年を選んでね：", bg="#f9f3f9").pack()
        grade_box = ttk.Combobox(self.root, textvariable=self.grade_var, values=grades, font=("Helvetica", 12))
        grade_box.current(0)
        grade_box.pack(pady=10)

        parts_of_speech = ["すべて", "名詞", "動詞", "形容詞", "副詞", "前置詞", "接続詞", "数詞", "助動詞", "代名詞"]
        tk.Label(self.root, text="品詞を選んでね：", bg="#f9f3f9").pack()
        pos_box = ttk.Combobox(self.root, textvariable=self.pos_var, values=parts_of_speech, font=("Helvetica", 12))
        pos_box.current(0)
        pos_box.pack(pady=10)

        tk.Button(self.root, text="スタート！", font=("Helvetica", 14), bg="#ffe0f0", command=self.start_quiz).pack(pady=20)

    def start_quiz(self):
        self.filtered_df = self.df.copy()
        grade = self.grade_var.get()
        pos = self.pos_var.get()

        if grade != "全学年":
            if grade == "中１のみ":
                self.filtered_df = self.filtered_df[self.filtered_df.iloc[:, 8].between(1000, 1999)]
            elif grade == "中２のみ":
                self.filtered_df = self.filtered_df[self.filtered_df.iloc[:, 8].between(2000, 2999)]
            elif grade == "中３のみ":
                self.filtered_df = self.filtered_df[self.filtered_df.iloc[:, 8].between(3000, 3999)]
            elif grade == "中１～２":
                self.filtered_df = self.filtered_df[self.filtered_df.iloc[:, 8].between(1000, 2999)]

        if pos != "すべて":
            pos_dict = {
                "名詞": "名", "動詞": "動", "形容詞": "形", "副詞": "副",
                "前置詞": "前", "接続詞": "接", "数詞": "数", "助動詞": "助", "代名詞": "代"
            }
            self.filtered_df = self.filtered_df[self.filtered_df.iloc[:, 3] == pos_dict[pos]]

        self.questions = self.filtered_df.sample(n=min(self.total_q, len(self.filtered_df))).reset_index(drop=True)
        self.score = 0
        self.q_num = 0
        self.clear_screen()
        self.show_question()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_question(self):
        if self.q_num >= self.total_q:
            self.show_result()
            return

        row = self.questions.iloc[self.q_num]
        word = row[2]
        correct = row[4]
        pos = row[3]

        # 同じ品詞から選択肢を選ぶ
        candidates = self.filtered_df[self.filtered_df.iloc[:, 3] == pos].sample(n=3)
        choices = list(candidates.iloc[:, 4])
        if correct not in choices:
            choices[random.randint(0, 2)] = correct
        random.shuffle(choices)

        tk.Label(self.root, text=f"{self.q_num + 1} / {self.total_q}", font=("Helvetica", 12), bg="#f9f3f9").pack()
        tk.Label(self.root, text=f"「{word}」の意味は？", font=("Helvetica", 20), bg="#f9f3f9", fg="#663366").pack(pady=(20, 5))

        tk.Button(self.root, text="🔊 発音", command=lambda: self.speak_word(word),
                  font=("Helvetica", 12), bg="#e0f7ff", fg="#003366").pack(pady=(0, 20))

        for choice in choices:
            tk.Button(self.root, text=choice, font=("Helvetica", 14), bg="#ffe4ec",
                      command=lambda c=choice: self.check_answer(c, correct)).pack(pady=5)

    def check_answer(self, selected, correct):
        if selected == correct:
            self.score += 1
        self.q_num += 1
        self.clear_screen()
        self.show_question()

    def show_result(self):
        self.clear_screen()
        tk.Label(self.root, text="結果発表！", font=("Helvetica", 22, "bold"), bg="#f9f3f9", fg="#cc3366").pack(pady=30)
        tk.Label(self.root, text=f"スコア： {self.score} / {self.total_q}", font=("Helvetica", 20), bg="#f9f3f9").pack(pady=10)
        tk.Button(self.root, text="もう一度", command=self.restart, font=("Helvetica", 14), bg="#d0f0f0").pack(pady=20)

    def restart(self):
        self.clear_screen()
        self.setup_start_screen()

    def speak_word(self, word):
        engine = pyttsx3.init()
        engine.setProperty('rate', 130)
        engine.setProperty('volume', 1.0)
        engine.say(word)
        engine.runAndWait()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChutanApp(root)
    root.mainloop()
