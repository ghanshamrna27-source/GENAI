while True:

    print("\n===== GITGURU =====")

    print("1. About GitGuru")
    print("2. Sample Git Questions")
    print("3. Git Command Rule Check")
    print("0. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":

        print("GitGuru helps beginners learn Git and GitHub.")

    elif choice == "2":

        print("1. What is Git?")
        print("2. What is GitHub?")
        print("3. How to clone a repository?")
        print("4. How to push code to GitHub?")

    elif choice == "3":

        command = input("Enter Git command: ")

        if command == "git clone":
            print("Used to copy a remote repository locally.")

        elif command == "git push":
            print("Used to upload local commits to a remote repository.")

        elif command == "git pull":
            print("Used to fetch and integrate remote changes.")

        else:
            print("Command not available in this demo.")

    elif choice == "0":

        print("Thank you for using GitGuru!")

        break

    else:

        print("Invalid choice. Try again.")