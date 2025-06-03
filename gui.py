import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext


class ReconFTWGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("reconFTW GUI")
        self.geometry("600x400")

        tk.Label(self, text="Target Domain").grid(row=0, column=0, sticky="w")
        self.domain_entry = tk.Entry(self, width=40)
        self.domain_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Targets List").grid(row=1, column=0, sticky="w")
        self.list_entry = tk.Entry(self, width=40)
        self.list_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self, text="Browse", command=self.browse_list).grid(row=1, column=2)

        tk.Label(self, text="Mode").grid(row=2, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="-r")
        modes = [("Recon", "-r"),
                 ("Subdomains", "-s"),
                 ("Passive", "-p"),
                 ("All", "-a"),
                 ("Web", "-w"),
                 ("OSINT", "-n")]
        mode_frame = tk.Frame(self)
        mode_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        for text, val in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=val).pack(side="left")

        tk.Button(self, text="Run", command=self.run_tool).grid(row=3, column=1, pady=10)

        self.output_text = scrolledtext.ScrolledText(self, width=70, height=15)
        self.output_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def browse_list(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.list_entry.delete(0, tk.END)
            self.list_entry.insert(0, filename)

    def run_tool(self):
        cmd = ['./reconftw.sh', self.mode_var.get()]
        domain = self.domain_entry.get().strip()
        if domain:
            cmd.extend(['-d', domain])
        targets_list = self.list_entry.get().strip()
        if targets_list:
            cmd.extend(['-l', targets_list])
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Running: {' '.join(cmd)}\n")
        self.update()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            self.output_text.insert(tk.END, line)
            self.output_text.see(tk.END)
            self.update()
        process.wait()
        self.output_text.insert(tk.END, f"\nProcess exited with code {process.returncode}\n")


if __name__ == '__main__':
    app = ReconFTWGUI()
    app.mainloop()
