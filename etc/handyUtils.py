import re

def python_stepen(stepen: str):
    stepeni = {
                "¹": "**1",
                "²": "**2",
                "³": "**3",
                "⁴": "**4",
                "⁵": "**5",
                "⁶": "**6",
                "⁷": "**7",
                "⁸": "**8",
                "⁹": "**9",
                "⁰": "**0"
              }
    result = ""

    # Define stepen'
    for i in stepen:
        if i in stepeni:
            result += stepeni[i]
        else:
            result += i

    return result

def convertBeforeProccessing(string: str):
    result = string

    for stepen in re.findall("[0-9]+[¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁰]", result):
        result = result.replace(stepen, "(" + python_stepen(stepen) + ")")
    for stepen in re.findall("[0-9]+\)[¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁰]", result):
        result = result.replace(stepen, python_stepen(stepen.replace(")", "")) + ")")

    # Skobki reshaem
    for i in range(0, 10):
        if f"{i}(" in result:
            result = result.replace(f"{i}(", f"{i}*(")
        elif f"){i}" in result:
            result = result.replace(f"){i}", f")*{i}")
        else:
            pass

    # Nu davaite poprobuem chislo Pi
    result = result.replace("π", "3.14")

    # V calculatore est kakayata bukva e, v dushe ne ebu chto ona znachit, no vidimo nada)
    result = result.replace("e", "2.718281828459")

    # Convertim korni
    for koren in re.findall("√\d+(?:\.\d+)?", result):
        result = result.replace(koren, koren.split("√")[1] + "**(1./2)")
    for koren in re.findall("√\([0-9]*\.?[0-9]+\*\*[0-9]*\)", result):
        result = result.replace(koren, koren.split("√")[1] + "**(1./2)")

    return result

