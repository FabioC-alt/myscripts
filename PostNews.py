import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QScrollArea, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
import feedparser
import webbrowser
import requests
from io import BytesIO
from bs4 import BeautifulSoup

class FetchNewsThread(QThread):
    news_fetched = pyqtSignal(list)

    def run(self):
        try:
            # Fetch news from Il Post feed
            feed = feedparser.parse('https://www.ilpost.it/feed')
            news_items = []
            for entry in feed.entries:
                # Extract the title and link
                title = entry.title
                link = entry.link

                # Extract the image URL from the description
                soup = BeautifulSoup(entry.description, 'html.parser')
                img_tag = soup.find('img')  # Find the first image tag
                image_url = img_tag['src'] if img_tag else None

                news_items.append({
                    'title': title,
                    'link': link,
                    'image_url': image_url
                })
            self.news_fetched.emit(news_items)
        except Exception as e:
            self.news_fetched.emit([{
                'title': f"Error fetching news: {str(e)}",
                'link': '',
                'image_url': None
            }])

class NewsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('News and Podcasts')
        self.setGeometry(100, 100, 600, 400)

        # Main layout
        layout = QVBoxLayout()

        # Scroll area to contain news items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.container = QWidget()
        self.news_layout = QVBoxLayout()  # Layout for news items
        self.container.setLayout(self.news_layout)

        # Set the scroll area widget
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        # Set the main layout in a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initialize variables for news items and selected index
        self.news_widgets = []
        self.selected_index = 0

        # Fetch news in a separate thread
        self.fetch_news()

    def fetch_news(self):
        self.thread = FetchNewsThread()
        self.thread.news_fetched.connect(self.display_news)
        self.thread.start()

    def display_news(self, news_items):
        # Clear old news labels if any
        for widget in self.news_widgets:
            widget.deleteLater()
        self.news_widgets = []

        # Show all news items
        for item in news_items:  # Display all items
            news_widget = self.create_news_widget(item)
            self.news_layout.addWidget(news_widget)
            self.news_widgets.append(news_widget)

        # Highlight the first news item by default if available
        if self.news_widgets:
            self.selected_index = 0
            self.update_highlight()

    def create_news_widget(self, news_item):
        """Creates a QWidget with title and image for a news item."""
        widget = QWidget()
        layout = QHBoxLayout()

        # Create and set news image (if available)
        image_label = QLabel()
        if news_item['image_url']:
            try:
                response = requests.get(news_item['image_url'])
                if response.status_code == 200:
                    image = QPixmap()
                    image.loadFromData(BytesIO(response.content).read())
                    image_label.setPixmap(image.scaled(100, 100, Qt.KeepAspectRatio))
                    image_label.mouseDoubleClickEvent = lambda event: self.open_link(news_item['link'])  # Make image clickable
                else:
                    print(f"Image request failed with status code {response.status_code}")
            except Exception as e:
                print(f"Failed to load image: {e}")
        else:
            image_label.setText("No image available")  # Display text when no image is available

        layout.addWidget(image_label)

        # Create and set news title
        title_label = QLabel(news_item['title'])
        title_label.setFont(QFont("Arial", 14))
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignLeft)  # Align title to the left
        layout.addWidget(title_label)

        # Set stretch factors to ensure the title aligns properly
        layout.setStretch(0, 0)  # Image will not stretch
        layout.setStretch(1, 1)  # Title will take available space

        # Store the link in the widget for later access
        widget.link = news_item['link']

        # Enable double-click interaction to open the link from the title
        title_label.mouseDoubleClickEvent = lambda event: self.open_link(news_item['link'])

        # Set layout
        widget.setLayout(layout)

        return widget

    def open_link(self, link):
        """Open the news link in a web browser."""
        if link:
            webbrowser.open(link)

    def update_highlight(self):
        """Highlight the selected news item and reset others."""
        for i, widget in enumerate(self.news_widgets):
            if i == self.selected_index:
                widget.setStyleSheet("background-color: lightblue;")
            else:
                widget.setStyleSheet("background-color: none;")

    def keyPressEvent(self, event):
        """Handle key press events to move between news items."""
        if event.key() == Qt.Key_Down:
            if self.selected_index < len(self.news_widgets) - 1:
                self.selected_index += 1
                self.update_highlight()
                self.scroll_to_selected()
        elif event.key() == Qt.Key_Up:
            if self.selected_index > 0:
                self.selected_index -= 1
                self.update_highlight()
                self.scroll_to_selected()

    def scroll_to_selected(self):
        """Scroll to the selected news item."""
        selected_widget = self.news_widgets[self.selected_index]
        self.scroll_area.ensureWidgetVisible(selected_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NewsApp()
    ex.show()
    sys.exit(app.exec_())
