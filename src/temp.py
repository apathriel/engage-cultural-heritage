from pathlib import Path
import rpy2.robjects as robjects

def main():
    r_file_path = Path(__file__).resolve().parents[0] / "test.r"
    
    r = robjects.r

    r.source(str(r_file_path))

    r_function = r["test_function"]

    result = r_function()

    print(f"Result from R script: {result}")

    print("R script executed successfully")
if __name__ == "__main__":
    main()