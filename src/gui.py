import os
import pkgutil
import queue
import shutil
import sys
import tempfile
import threading
import tkinter
import tkinter.filedialog
import tkinter.scrolledtext
import tkinter.simpledialog
import tkinter.ttk

from uploader import Uploader
from licensetext import licenseTexts
from version import versionString


class ThreadSafeLabel(tkinter.Label):
    def __init__(self, master, **options):
        tkinter.Label.__init__(self, master, **options)
        self.queue = queue.Queue()
        self.update_me()

    def write(self, string):
        self.queue.put(string)

    def clear(self, string):
        self.queue.put(string)

    def update_me(self):
        try:
            while 1:
                string = self.queue.get_nowait()
                if string is None:
                    self.configure(text='')
                else:
                    self.configure(text=string)
                self.update_idletasks()
        except queue.Empty:
            pass
        self.after(100, self.update_me)


class ThreadSafeProgressbar(tkinter.ttk.Progressbar):
    def __init__(self, master, **options):
        tkinter.ttk.Progressbar.__init__(self, master, **options)
        self.queue = queue.Queue()
        self.update_me()

    def update(self, amount=1.0):
        self.queue.put(amount)

    def clear(self):
        self.queue.put(None)

    def update_me(self):
        try:
            while 1:
                amount = self.queue.get_nowait()
                if amount is None:
                    self.configure(value=0)
                else:
                    self.step(amount)
                self.update_idletasks()
        except queue.Empty:
            pass
        self.after(100, self.update_me)


class ThreadSafeConsole(tkinter.scrolledtext.ScrolledText):
    def __init__(self, master, **options):
        tkinter.scrolledtext.ScrolledText.__init__(self, master, **options)
        self.queue = queue.Queue()
        self.update_me()

    def write(self, line):
        self.queue.put(line)

    def clear(self):
        self.queue.put(None)

    def update_me(self):
        try:
            while 1:
                line = self.queue.get_nowait()
                self.configure(state='normal')
                if line is None:
                    self.delete(1.0, tkinter.END)
                else:
                    self.insert(tkinter.END, str(line))
                self.see(tkinter.END)
                self.configure(state='disabled')
                self.update_idletasks()
        except queue.Empty:
            pass
        self.after(100, self.update_me)


class progress:
    def __init__(self, output, progress):
        self._maximum = 0
        self._total = 0
        self._out = output
        self._progress = progress
        self._progress.configure(value=0)
        self._prev_percent = -1

    def __call__(self, amount):
        self._total += amount
        percent = int(self._total * 100 / self._maximum)
        if percent != self._prev_percent:
            self._out.write('{}: {} / {} ({}%)'.format(self._label,
                                                       self._total, self._maximum, percent))
            self._progress.configure(value=self._total)
            self._prev_percent = percent

    def init(self, total, label):
        self._label = label
        self._out.write(label)
        self._progress.configure(maximum=total, value=0)
        self._maximum = total
        self._prev_percent = -1

    def finish(self):
        self._out.write('{}: finished'.format(self._label))
        self._maximum = 0
        self._prev_percent = -1
        self._total = 0
        self._progress.configure(value=0)


class AboutDialog(tkinter.simpledialog.Dialog):

    def buttonbox(self):
        box = tkinter.Frame(self)

        w = tkinter.Button(box, text="OK", width=10,
                           command=self.ok, default=tkinter.ACTIVE)
        w.pack(side=tkinter.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        box.pack()

    def body(self, master):
        self.message = tkinter.scrolledtext.ScrolledText(master, height=30)
        self.message.grid(sticky='we', padx=2, pady=2)
        for line in licenseTexts:
            self.message.insert(tkinter.END, line + '\n')
        return self.message


def about():
    message = '\n'.join([])
    MyDialog(None)


class UploaderApp(tkinter.Tk):
    def about(self):
        message = '\n'.join([])
        AboutDialog(self)

    def console_out(self, string):
        self.output.write(string + '\n')

    def __init__(self, *args, **kwargs):
        self._endpoint = os.getenv(
            "NNC_ENDPOINT", 'https://console-api.dl.sony.com')
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.resizable(1, 0)
        self.title('Neural Network Console Uploader')
        self.grid_columnconfigure(1, weight=1)

        menubar = tkinter.Menu(self)

        filemenu = tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        helpmenu = tkinter.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='About', command=self.about)
        menubar.add_cascade(label='Help', menu=helpmenu)

        self.config(menu=menubar)

        # Row 0
        tokenLabel = tkinter.Label(self, text='token')
        tokenLabel.grid(row=0, column=0, columnspan=1, padx=2, pady=2)

        self.tokenText = tkinter.Entry(self, state='disabled')
        self.tokenText.grid(row=0, column=1, columnspan=4,
                            sticky='we', padx=2, pady=2)

        self.tokenButton = tkinter.Button(
            self, text='Paste', command=self.pastetoken)
        self.tokenButton.grid(row=0, column=5, columnspan=1, padx=2, pady=2)

        # Row 1
        fileLabel = tkinter.Label(self, text='file')
        fileLabel.grid(row=1, column=0, columnspan=1, padx=2, pady=2)

        self.fileText = tkinter.Entry(self, state='disabled')
        self.fileText.grid(row=1, column=1, columnspan=4,
                           sticky='we', padx=2, pady=2)

        self.fileButton = tkinter.Button(
            self, text='Select', command=self.selectfile)
        self.fileButton.grid(row=1, column=5, columnspan=1, padx=2, pady=2)

        # Row 2
        self.startButton = tkinter.ttk.Button(text="start", command=self.start)
        self.startButton.grid(row=2, column=0, columnspan=6,
                              sticky='we', padx=2, pady=2)

        # Row 3
        self.output = ThreadSafeConsole(self, state='disabled', height=20)
        self.output.grid(row=3, column=0, columnspan=6,
                         sticky='we', padx=2, pady=2)

        # Row 4
        self.progressbar = ThreadSafeProgressbar(self, mode='determinate')
        self.progressbar.configure(maximum=100, value=0)
        self.progressbar.grid(row=4, columnspan=7, sticky='we', padx=2, pady=2)

        # Row 5
        self.progressText = ThreadSafeLabel(self)
        self.progressText.grid(row=5, columnspan=7,
                               sticky='we', padx=2, pady=2)

        if sys.platform == 'win32':
            iconpath = None
            try:
                iconpath = os.path.abspath(os.path.join(
                    sys._MEIPASS, 'img', 'uploader.ico'))
            except AttributeError:
                iconpath = os.path.abspath(os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), '..', 'img', 'uploader.ico'))
            if os.path.isfile(iconpath):
                self.iconbitmap(iconpath)
        elif sys.platform == 'linux':
            iconpath = None
            try:
                iconpath = os.path.abspath(os.path.join(
                    sys._MEIPASS, 'img', 'uploader.xbm'))
            except AttributeError:
                iconpath = os.path.abspath(os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), '..', 'img', 'uploader.xbm'))
            if os.path.isfile(iconpath):
                self.iconbitmap('@{}'.format(iconpath))
        self.console_out('Uploader ({})'.format(versionString))

    def pastetoken(self):
        clipboard = self.clipboard_get()
        self.tokenText.configure(state='normal')
        self.tokenText.delete(0, tkinter.END)
        self.tokenText.insert(tkinter.END, clipboard)
        self.tokenText.configure(state='disabled')

    def selectfile(self):
        name = tkinter.filedialog.askopenfilename(
            filetypes=[('CSV dataset', '*.csv')])
        self.fileText.configure(state='normal')
        self.fileText.delete(0, tkinter.END)
        self.fileText.insert(tkinter.END, name)
        self.fileText.configure(state='disabled')

    def stop(self):
        print("STOP!!!!!!!!!!!!!!")
        pass

    def start(self):
        upload = threading.Thread(target=self.upload, name='upload')
        self.tokenButton.configure(state='disabled')
        self.fileButton.configure(state='disabled')
        self.startButton.configure(text='stop', command=self.stop)
        upload.start()

    def upload(self):

        uploader = Uploader(log=self.console_out,
                            progress=progress(self.progressText, self.progressbar))

        filename = self.fileText.get()
        name = os.path.splitext(os.path.basename(filename))[0]
        uploader.upload(self.tokenText.get(), filename,
                        name, self.uploadFinished, endpoint=self._endpoint)

    def uploadFinished(self, state):
        self.tokenButton.configure(state='normal')
        self.fileButton.configure(state='normal')
        self.startButton.configure(text='start', command=self.start)


app = UploaderApp()
app.mainloop()
