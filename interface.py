from bs4 import BeautifulSoup
import json
from querier import Querier
from tkinter import *
import urllib.request
import webbrowser


class Interface:
    def __init__(self, querier):
        window = Tk()
        window.title("Search Engine")
        window.geometry('960x600')
        # Creates Frame for user entry
        top_frame = LabelFrame(window, text="Enter Search Query")
        top_frame.pack(pady=10)
        # User entry Widget
        input_box = Entry(top_frame, font=("Helvetica", 14), width=47)
        input_box.pack(pady=20, padx=20)
        # Frame that will display
        text_frame = Frame(window)
        text_frame.pack(pady=5)
        # Scroll bar configuration
        y_scroll = Scrollbar(text_frame)
        y_scroll.pack(side=RIGHT, fill=Y)
        x_scroll = Scrollbar(text_frame, orient='horizontal')
        x_scroll.pack(side=BOTTOM, fill=X)
        # Text display widget
        text = Text(text_frame, yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        y_scroll.config(command=text.yview)
        x_scroll.config(command=text.xview)
        text.pack()

        # Frame for Search and clear buttons
        buttons = Frame(window)
        buttons.pack(pady=10)


        def callback(url):
            webbrowser.open_new_tab(url)


        def create_hyperlink(url):
            """
            Creates the configurations for the hyperlinks.
            Binds the link to a tag to be used when inserted into the text frame
            Tags are the url to specify the which configurations to use
            """
            tag = url
            text.tag_config(tag, foreground="blue", underline=1)
            text.tag_bind(tag, "<Enter>", text.config(cursor="hand2"))
            link = "http://" + url
            text.tag_bind(tag, "<Button-1>", lambda x: callback(link))


        def search():
            """
            Function inserts the search results into the text widget.
            It calls retrieve in the querier class to get the query results.
            """
            text.delete(0.0, END)
            links = []
            # Takes the query from the user and retrieves the query results.
            results = querier.retrieve(input_box.get())[:20]
            count = 1
            text.insert(END, "\n")
            for docID, url in results:
                text.insert(END, count)
                text.insert(END, "\n")
                text.insert(END, "URL: ")
                # Configures the URL
                create_hyperlink(url)
                # URL is passed as a tag
                text.insert(END, url, url)
                text.insert(END, "\n")
                count += 1
                try:
                    with open("WEBPAGES_RAW/" + docID) as file:
                        soup = BeautifulSoup(file, "lxml")

                        # Display the webpage's title if it exists
                        text.insert(END, "TITLE: ")
                        if soup.title and soup.title.string:
                            text.insert(END, soup.title.string.strip())
                        else:
                            text.insert(END, "No Title")
                        text.insert(END, "\n")
        
                        meta_data = soup.find_all("meta")

                        # Display the webpage's description if it exists
                        desc_exist = False
                        for t in meta_data:
                            if t.get('name'):
                                if t.get('name') == "description":
                                    text.insert(END, "DESC: ")
                                    text.insert(END, t.get('content'))
                                    text.insert(END, "\n")
                                    desc_exist = True
                            if t.get('http-equiv'):
                                if t.get('http-equiv') == 'DESCRIPTION':
                                    text.insert(END, "DESC: ")
                                    text.insert(END, t.get('content'))
                                    text.insert(END, "\n")
                                    desc_exist = True

                        # Display a preview of the webpage's content if the
                        # webpage's description doesn't exist.
                        if not desc_exist:
                            text.insert(END, "Text summary: ")
                            text.insert(END, "\n")
                            for s in soup(["script"]):
                                s.extract()
                            raw_txt = soup.get_text()
                            lines = raw_txt.splitlines()
                            for line in lines:
                                line.strip()
                            blocks = (block.strip() for line in lines for block in line.split("  "))
                            new_txt = '/n'.join(block for block in blocks if block)
                            short_txt = new_txt[:240]
                            short_txt = short_txt + "..."
                            text.insert(END, short_txt)
                            text.insert(END, "\n")

                except:
                    text.insert(END, "404 ERROR")

                text.insert(END, "\n")
                text.insert(END, "\n")


        def clear_text():
            """
            Clears the contents of the text widget when the clear button is
            clicked.
            """
            text.delete(0.0, END)
            input_box.delete(0, END)


        # Button configuration and binding to functions
        search_button = Button(buttons, text="Search", font=("Helvetica", 20), command=search)
        search_button.grid(row=0, column=0, padx=20)

        clear_button = Button(buttons, text="Clear", font=("Helvetica", 20), command=clear_text)
        clear_button.grid(row=0, column=1)

        window.mainloop()
