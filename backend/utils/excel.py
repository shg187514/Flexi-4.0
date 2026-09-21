import io
import pandas as pd
import msoffcrypto


def read_any_excel(file_obj, password=None):
    """
    Robustly read any Excel file (.xlsx, .xls, HTML-Excel, CSV, encrypted Excel).
    Handles password-protected Excel files using msoffcrypto-tool.
    """
    if hasattr(file_obj, "read"):
        content = file_obj.read()
    elif isinstance(file_obj, (bytes, bytearray)):
        content = file_obj
    else:
        with open(file_obj, "rb") as f:
            content = f.read()

    # Check if file is encrypted with msoffcrypto
    is_encrypted = False
    try:
        stream = io.BytesIO(content)
        office_file = msoffcrypto.OfficeFile(stream)
        is_encrypted = office_file.is_encrypted()
    except Exception:
        is_encrypted = False

    if is_encrypted:
        passwords_to_try = []
        if password:
            passwords_to_try.append(password)
        # Try common/default empty passwords first
        passwords_to_try.extend(["Velociraptor", "", "1234", "password", "admin", "flexi", "Flexi", "123456"])

        decrypted = io.BytesIO()
        decrypted_success = False
        for pwd in passwords_to_try:
            try:
                stream = io.BytesIO(content)
                office_file = msoffcrypto.OfficeFile(stream)
                office_file.load_key(password=pwd)
                decrypted.seek(0)
                decrypted.truncate()
                office_file.decrypt(decrypted)
                decrypted.seek(0)
                for eng in ["openpyxl", "xlrd", None]:
                    try:
                        decrypted.seek(0)
                        return pd.read_excel(decrypted, engine=eng) if eng else pd.read_excel(decrypted)
                    except Exception:
                        pass
                decrypted_success = True
                break
            except Exception:
                pass

        if not decrypted_success:
            if password:
                raise ValueError("Incorrect password for encrypted Excel file.")
            else:
                raise ValueError("This Excel file is password-protected. Please enter the file password to open it.")

    # 1. Try standard pandas read_excel engines for unencrypted files
    for engine in ["openpyxl", "xlrd", None]:
        try:
            stream = io.BytesIO(content)
            if engine:
                return pd.read_excel(stream, engine=engine)
            else:
                return pd.read_excel(stream)
        except Exception:
            pass

    # 2. Try reading as HTML table (Excel HTML export format)
    try:
        stream = io.BytesIO(content)
        dfs = pd.read_html(stream)
        if dfs and len(dfs) > 0:
            return dfs[0]
    except Exception:
        pass

    # 3. Try reading as CSV (CSV files saved with .xls or .xlsx extension)
    try:
        stream = io.BytesIO(content)
        return pd.read_csv(stream)
    except Exception:
        pass

    raise ValueError("Unable to read Excel file. Please ensure it is a valid .xlsx or .xls file.")
