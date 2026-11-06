product = "GitGuru"
user = "Students, beginners, and developers learning Git and GitHub"
problem = "Beginners struggle with Git commands, repositories, commits, branches, merging, and troubleshooting."
data_source = "Official Git and GitHub documentation"

print(f"PRODUCT: {product}")
print(f"USER: {user}")
print(f"PROBLEM: {problem}")
print(f"DATA SOURCE: {data_source}")

name = input("\\nWhat is your name? ").strip()
question = input("What would you like to know about Git or GitHub? ").strip()
print(f"Hello, {name or 'learner'}!")
print(f"Your question: {question or 'No question entered.'}")
