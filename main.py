from project_assistant.suggester import suggest_code_improvement
import sys
import os
import argparse

def default_test():
    from ai_engine.interface import query_llama
    print(query_llama("Write a Python function that returns True if a number is prime."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Suggest code improvements or run a default test query.",
        epilog="Example: python main.py suggest myscript.py --task optimize"
    )
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0', help='Show program version and exit.')
    subparsers = parser.add_subparsers(dest='command', required=False)

    # Suggest subcommand
    suggest_parser = subparsers.add_parser('suggest', help="Get code suggestions for a file.")
    suggest_parser.add_argument('filename', help="The file to analyze for suggestions.")
    suggest_parser.add_argument('--task', choices=["refactor", "optimize", "explain"], default="refactor", help="Type of suggestion: refactor, optimize, or explain. Default is refactor.")
    suggest_parser.add_argument('--out', type=str, default=None, help="Optional output file to write suggestions.")

    # Check subcommand
    check_parser = subparsers.add_parser('check', help="Check folder integrity.")
    check_parser.add_argument('--fix', action='store_true', help="Automatically create missing required folders.")
    check_parser.add_argument('--json', action='store_true', help="Output folder integrity results as JSON.")

    # Init subcommand
    init_parser = subparsers.add_parser('init', help="Scaffold a new microservice.")
    init_parser.add_argument('servicename', help="The name of the microservice to initialize.")
    init_parser.add_argument('--git', dest='git', action='store_true', help="Initialize a git repository in the new service directory.")
    init_parser.add_argument('--no-git', dest='git', action='store_false', help="Do not initialize git (default).")
    init_parser.set_defaults(git=False)

    # Run subcommand
    run_parser = subparsers.add_parser('run', help="Run a service (Node or Python)")
    run_parser.add_argument('service', help="Service name or path to run.")
    run_parser.add_argument('--watch', action='store_true', help="Restart on file changes.")

    args = parser.parse_args()

    # Early default test fallback
    if not args.command:
        default_test()
        sys.exit(0)

    if args.command == "check":
        from project_assistant.folder_checker import check_folder_integrity
        issues = check_folder_integrity(fix=getattr(args, 'fix', False), output_json=getattr(args, 'json', False))
        if issues:
            if not getattr(args, 'json', False):
                print("\n=== Folder Integrity Issues ===\n")
                for issue in issues:
                    print(issue)
                print(f"\nSummary: {len(issues)} issue(s) found.")
            sys.exit(1)
        else:
            if not getattr(args, 'json', False):
                print("✅ Folder structure looks good.")
                print("Summary: No issues found.")
            sys.exit(0)
    elif args.command == "suggest":
        output = suggest_code_improvement(args.filename, args.task)
        output = f"\n=== Suggested Improvements ({args.task}) ===\n\n{output}"
        if args.out:
            with open(args.out, "w", encoding="utf-8") as outf:
                outf.write(output)
            print(f"Suggestions written to {args.out}")
        else:
            print(output)
        sys.exit(0)
    elif args.command == "init":
        from project_assistant.scaffolder import create_microservice
        create_microservice(args.servicename, git=args.git)
        sys.exit(0)
    elif args.command == "run":
        from run_helper import run
        sys.exit(run(args))
    else:
        print(f"[WARN] Unknown command '{args.command}'. Running default test.\n")
        default_test()
        sys.exit(1)
