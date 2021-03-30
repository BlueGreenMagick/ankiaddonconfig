# ankiaddonconfig

## Installing with Git Submodule
To use this package, run the following command.

```bash
git submodule add https://github.com/BlueGreenMagick/ankiaddonconfig.git 

```
If you want to use this package in a different directory, pass the directory path to the command like below.

```bash
git submodule add https://github.com/BlueGreenMagick/ankiaddonconfig.git src/addon
```

When you want to pull the changes made in this repo, run the below command. If you installed this package into a different directory, replace `ankiaddonconfig` to the path of the package directory.
```bash
git submodule update --remote ankiaddonconfig
```

You may also want to instruct people that after cloning your project, they will need to run the following line.
```bash
git submodule update --init
```

## Using ConfigManager
```python
from .ankiaddon import ConfigManager
conf = ConfigManager()

fruit = conf["fruit"]

conf["fruit"] = "apple"
conf.save() # Save conf to disk
```

If you have a dictionary in your config, you can also do this:
```python
value = conf.get("apple.color", "#ff0000") # conf["apple.color"] will raise KeyError if it doesn't exist
conf["apple.color"] = "#ffff00"

apple_color = conf.pop("apple.color")
del conf["apple.size"]
```

Other features:
```python
conf.load() # discards current config and loads config from disk.
conf.get_default("fruit") # returns the value set in config.json
conf.to_json() # returns a json copy of the config
conf.clone() # returns a deepcopy of the config dictionary
```

## Creating custom config window

This package was born out of a desire to make creating a gui config window as painless as possible.

### Examples
You can create a checkbox with the following code: `.checkbox("conf_key", "description")`.
This package then takes care of syncing the config to the widget state. 
So when the user modifies the checkbox state, the ConfigManager is automatically synced to the checkbox state.

When the user saves the changes, `conf.save()` is called. If cancelled, `conf.load()` to discard the modified config.

```python
from ankiaddon import ConfigManager, ConfigWindow

conf = ConfigManager()

def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")
    tab.text("Addon Config")
    tab.checkbox("use_fruit", "Should this addon use a fruit?")
    
    fruit_labels = ["Apples", "Pears", "Grapes"] # Shown to the user in the config window
    fruit_values = ["apple", "pear", "grape"] # Actual value the json config will have
    tab.dropdown("fruit", fruit_labels, fruit_values)

    apple_color_row.color_input("apple.color", "Color of the apple:")

    # If you are not sure what this does,
    # Try resizing the config window without this line
    tab.stretch(1) 

conf.use_custom_window()
conf.add_config_tab(general_tab)
```

### Documentation
List of all inputs. Each of the inputs are linked to a single config data.

```python
def checkbox(self, key: str, description: str = "") -> QCheckBox:
    assert isinstance(conf[key], bool)
def dropdown(self, key: str, labels: list, values: list, description: Optional[str] = None) -> QComboBox:
    assert conf[key] in values
def text_input(self, key: str, description: Optional[str] = None) -> QLineEdit:
    assert isinstance(conf[key], str)
def color_input(self, key: str, description: Optional[str] = None) -> QPushButton:
    assert conf[key] is 'a hex color string like "#000", "#000000" that QColor can understand'
```

List of all widgets:
```python
def label(self, label: str, bold: bool = False, size: int = 0, multiline: bool = True) -> QLabel:
    # Text label. `size`: font size
text = label
def hlayout(self) -> "ConfigLayout":
    # Horizontal layout
def vlayout(self) -> "ConfigLayout":
    # Vertical layout
def scroll_layout(self, horizontal: bool = True, vertical: bool = True) -> "ConfigLayout":
    # Scrollable layout
def space(self, space: int = 1) -> None:
    # Space between widgets
def stretch(self, factor: int = 0) -> None:
    # Stretch spacing for when window resizes
```