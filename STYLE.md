# Code Style

Most of the style guidelines can be checked, fixed, and enforced via Ruff. Older code may not be adhering to all of these guidelines, in which case _"do as I say, not as I do"..._

-   Do your best to write clear, concise, and modular code.
    - This should include making methods private by default (e.g. `__method()`)
    - Methods should only be protected (e.g. `_method()`) or public (e.g. `method()`) when needed and warranted
-   Keep a maximum column width of no more than **100** characters.
-   Code comments should be used to help describe sections of code that can't speak for themselves.
-   Use [Google style](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) docstrings for any classes and functions you add.
    -   If you're modifying an existing function that does _not_ have docstrings, you don't _have_ to add docstrings to it... but it would be pretty cool if you did ;)
-   Imports should be ordered alphabetically.
-   Lists of values should be ordered using their [natural sort order](https://en.wikipedia.org/wiki/Natural_sort_order).
    -   Some files have their methods ordered alphabetically as well (i.e. [`thumb_renderer`](https://github.com/TagStudioDev/TagStudio/blob/main/src/tagstudio/qt/widgets/thumb_renderer.py)). If you're working in a file and notice this, please try and keep to the pattern.
-   When writing text for window titles or form titles, use "[Title Case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case)" capitalization. Your IDE may have a command to format this for you automatically, although some may incorrectly capitalize short prepositions. In a pinch you can use a website such as [capitalizemytitle.com](https://capitalizemytitle.com/) to check.
-   If it wasn't mentioned above, then stick to [**PEP-8**](https://peps.python.org/pep-0008/)!

## QT
As of writing this section, the QT part of the code base is quite unstructured and the View and Controller parts are completely intermixed[^1]. This makes maintenance, fixes and general understanding of the code base quite challenging, because the interesting parts you are looking for are entangled in a bunch of repetitive UI setup code. To address this we are aiming to more strictly separate the view and controller aspects of the QT frontend.

The general structure of the QT code base should look like this:
```
qt
├── controller
│   ├── widgets
│   │   └── preview_panel_controller.py
│   └── main_window_controller.py
├── view
│   ├── widgets
│   │   └── preview_panel_view.py
│   └── main_window_view.py
├── ts_qt.py
└── mixed.py
```

In this structure there are the `view` and `controller` sub-directories. They have the exact same structure and for every `<component>_view.py` there is a `<component>_controller.py` at the same location in the other subdirectory and vice versa.

Typically the classes should look like this:
```py
# my_cool_widget_view.py
class MyCoolWidgetView(QWidget):
    def __init__(self):
        super().__init__()
        self.__button = QPushButton()
        self.__color_dropdown = QComboBox()
        # ...
        self.__connect_callbacks()
        
    def __connect_callbacks(self):
        self.__button.clicked.connect(self._button_click_callback)
        self.__color_dropdown.currentIndexChanged.connect(
            lambda idx: self._color_dropdown_callback(self.__color_dropdown.itemData(idx))
        )
    
    def _button_click_callback(self):
        raise NotImplementedError()
```
```py
# my_cool_widget_controller.py
class MyCoolWidget(MyCoolWidgetView):
    def __init__(self):
        super().__init__()
    
    def _button_click_callback(self):
        print("Button was clicked!")

    def _color_dropdown_callback(self, color: Color):
        print(f"The selected color is now: {color}")
```

Observe the following key aspects of this example:
- The Controller is just called `MyCoolWidget` instead of `MyCoolWidgetController` as it will be directly used by other code
- The UI elements are in private variables
  - This enforces that the controller shouldn't directly access UI elements
  - Instead the view should provide a protected API (e.g. `_get_color()`) for things like setting/getting the value of a dropdown, etc.
  - Instead of `_get_color()` there could also be a `_color` method marked with `@property` 
- The callback methods are already defined as protected methods with NotImplementedErrors
  - Defines the interface the callbacks
  - Enforces that UI events be handled

> [!NOTE]
> A good (non-exhaustive) rule of thumb is: If it requires a non-UI import, then it doesn't belong in the `*_view.py` file.

[^1]: For an explanation of the Model-View-Controller (MVC) Model, checkout this article: [MVC Framework Introduction](https://www.geeksforgeeks.org/mvc-framework-introduction/).
