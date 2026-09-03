import math
import re
from sympy import Eq, solve, symbols, sympify


def normalize_expression(text: str) -> str:
    """Cleans up raw user input so SymPy can evaluate it."""
    text = text.replace("π", "pi")
    text = text.replace("^", "**")
    text = text.replace("÷", "/")

    # Square roots & Logs
    text = re.sub(r"√\((.*?)\)", r"sqrt(\1)", text)
    text = re.sub(r"√(\d+)", r"sqrt(\1)", text)
    text = re.sub(r"Log\((.*?)\)", r"log(\1,10)", text)
    text = re.sub(r"Ln\((.*?)\)", r"log(\1)", text)

    # Convert implicit multiplication like 2x -> 2*x
    text = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", text)
    return text


def evaluate_expression(text: str, variables_dict: dict, mode: str):
    """Evaluates math based on the selected mode."""
    temp_expr = normalize_expression(text)

    try:
        if mode == "Algebra (Solve for X)":
            # Forces equation solving mode
            target = "==" if "==" in temp_expr else "="
            if target in temp_expr:
                l_str, r_str = temp_expr.split(target, 1)
                lhs = sympify(l_str, locals=variables_dict)
                rhs = sympify(r_str, locals=variables_dict)
            else:
                # If no '=' is typed, assume expression equals 0 (e.g. 2*x - 10 implies 2*x - 10 = 0)
                lhs = sympify(temp_expr, locals=variables_dict)
                rhs = 0

            x = symbols("x")
            sol = solve(Eq(lhs, rhs), x)
            return f"x = {sol}"

        elif mode == "Basic / Variable Assignment":
            # Variable storage (e.g., x = 10 or a = 5)
            if "=" in temp_expr and "==" not in temp_expr:
                name, val = temp_expr.split("=", 1)
                var_name = name.strip().lower()
                res = float(sympify(val, locals=variables_dict).evalf())

                # Store into variable dictionary
                variables_dict[var_name] = res
                return f"Saved Variable: {var_name} = {res}"
            else:
                # Direct arithmetic calculation
                total = sympify(temp_expr, locals=variables_dict)
                numeric_total = total.evalf()
                variables_dict["ans"] = float(numeric_total)
                return str(numeric_total)

    except Exception as e:
        return f"Error: {str(e)}"