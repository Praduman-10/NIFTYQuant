import importlib
import pkgutil
import pandas as pd
import engine.factors


def apply_factors(df: pd.DataFrame, spot: float):
    df = df.copy()
    package = engine.factors
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name == "__init__":
            continue
        module = importlib.import_module(f"engine.factors.{module_name}")
        if hasattr(module, "apply"):
            df = module.apply(df, spot)
    return df
