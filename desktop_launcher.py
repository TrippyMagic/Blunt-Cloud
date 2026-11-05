import sys

if __name__ == "__main__":
    if sys.argv[1:2] == ["--cli"]:
        del sys.argv[1]
        from bluntcloud.__main__ import main
    else:
        from bluntcloud.ui import main
    main()
