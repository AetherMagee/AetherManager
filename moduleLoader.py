import os
from importlib import util as imputil
from aethermanager import logger


def checkModuleIntegrity(pathToModule):
    checkedDirs = ["docs", "strings"]
    docsIntegrityPassed = False
    stringsIntegrityPassed = False
    mainFileIntegrityPassed = False
    try:
        for element in os.listdir(pathToModule):
            if os.path.isdir(pathToModule + "/" + element) and element in checkedDirs:
                if os.listdir(pathToModule + "/" + element) == ["help.py", "description.py"]:
                    docsIntegrityPassed = True
                if element == "strings" and os.listdir(pathToModule + "/" + element):
                    stringsIntegrityPassed = True
            elif element == "main.py":
                mainFileIntegrityPassed = True
        if mainFileIntegrityPassed and docsIntegrityPassed and stringsIntegrityPassed:
            return True
        return False
    except Exception as e:
        print(str(e))
        return False


def loadModule(pathToModule):
    path = pathToModule + "/main.py"
    name = path.replace("/main.py", "").replace("/",
                                                ".").replace("\\\\", ".").replace("\\", ".")
    logger.debug("Path: " + path)
    logger.debug("Name: " + name)
    specs = imputil.spec_from_file_location(name, path)
    mod = imputil.module_from_spec(specs)
    specs.loader.exec_module(mod)


def loadAllModules():
    logger.info("ModLoad started...")
    for element in os.listdir("modules"):
        if os.path.isdir("modules/" + element) and checkModuleIntegrity("modules/" + element):
            logger.info("Loading module " + element + "...")
            loadModule("modules/" + element)
