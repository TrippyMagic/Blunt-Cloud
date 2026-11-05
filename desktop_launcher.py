import sys

if __name__ == "__main__":
    if sys.argv[1:2] == ["--cli"]:
        del sys.argv[1]
        from bluntcloud.__main__ import main
    elif sys.argv[1:] == ["--smoke-desktop"]:
        from bluntcloud.ui import W, Window
        app = W.QApplication([])
        window = Window()
        window.vtk.GetRenderWindow().SetOffScreenRendering(1)
        window.vtk.GetRenderWindow().Render()
        window.close()
        sys.exit(0)
    else:
        from bluntcloud.ui import main
    main()
