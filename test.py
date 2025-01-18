import tkinter as tk

def get_multiline_input():
    def on_submit():
        nonlocal input_text
        input_text = text_widget.get("1.0", tk.END)
        root.destroy()

    root = tk.Tk()
    root.title("Input Text")

    text_widget = tk.Text(root, height=10, width=50)
    text_widget.pack()

    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack()

    input_text = ""
    root.mainloop()
    
    return input_text.strip()

text = get_multiline_input()
print("\nYou entered:")
print(text)
