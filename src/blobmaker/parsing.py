import json
from blobmaker.default_params import DEFAULTS
from blobmaker.generic_classes import CubismError
from blobmaker.assemblies import Assembly
from blobmaker.components import Component


def load_json(json_file) -> dict:
    """Load a json file to dict."""
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def get_subclass_from_classname(classname) -> Assembly | Component:
    """Return an Assembly or Component subclass by name."""
    subclasses = Assembly.__subclasses__() + Component.__subclasses__()
    for subclass in subclasses:
        if subclass.__name__ == classname:
            return subclass
    raise ValueError("No such class.")


def extract_if_string(possible_filename):
    if type(possible_filename) is str:
        return load_json(possible_filename)
    return possible_filename


def delve(component_obj: list | dict):
    if type(component_obj) is dict:
        return {comp_key: extract_if_string(comp_value) for comp_key, comp_value in component_obj.items()}
    elif type(component_obj) is list:
        return [extract_if_string(component) for component in component_obj]
    elif type(component_obj) is str:
        return load_json(component_obj)
    raise TypeError(f"Unrecognised delvee: {component_obj}")


class ParameterFiller():
    def __init__(self):
        self.log = []
        self.design_tree = {}
        self.config = {}

    def add_log(self, message: str):
        self.log.append(message)

    def process_design_tree(self, design_tree: dict):
        self.design_tree = design_tree
        self.__prereq_check()
        self.config = self.__get_config()
        if self.config:
            self.design_tree = self.__fill_params(self.design_tree, self.config)
        return self.design_tree

    def print_log(self):
        for message in self.log:
            print(message)

    def __prereq_check(self):
        try:
            if type(self.design_tree["class"]) is not str:
                raise CubismError("json object class must be a string")
        except KeyError:
            raise CubismError("All json objects need to have a class")

    def __get_config(self):
        for default_class in DEFAULTS:
            if default_class["class"].lower() == self.design_tree["class"].lower():
                return default_class
        self.add_log(f"Default configuration not found for: {self.design_tree['class']}")
        return False

    def __fill_params(self, design_tree: dict, config: dict):
        design_tree = self.__setup_tree(design_tree)
        for key, default_value in config.items():
            if key in design_tree.keys():
                if type(default_value) is dict:
                    design_tree[key] = self.__fill_params(design_tree[key], config[key])
                else:
                    self.add_log(f"{key} set to: {design_tree[key]} (default: {default_value})")
            else:
                self.design_tree[key] = default_value
                self.add_log(f"key {key} not specified. Added default.")
        self.__cleanup_logs(design_tree, config)
        return design_tree

    def __setup_tree(self, design_tree: dict):
        if "class" in design_tree.keys():
            self.add_log(f"---------- Logging class: {design_tree['class']} ----------")
        if "components" in design_tree.keys():
            design_tree["components"] = delve(design_tree["components"])
        return design_tree

    def __cleanup_logs(self, design_tree: dict, config: dict):
        for key in list(set(design_tree.keys()) - set(config.keys())):
            self.add_log(f"key {key} not in default config")
        if "class" in design_tree.keys():
            self.add_log(f"---------- Finished logging class: {design_tree['class']} ----------")

def get_format_extension(format_type: str):
    format_type = format_type.lower()
    if format_type == "cubit" or "cub5" in format_type:
        return ".cub5"
    elif format_type == "exodus" or ".e" in format_type:
        return ".e"
    elif format_type == "dagmc" or "h5m" in format_type:
        return ".h5m"
    elif format_type == "step" or "stp" in format_type:
        return ".stp"
    else:
        raise CubismError(f"Unrecognised format: {format_type}")