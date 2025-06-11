import time
from mpi4py import MPI
import sys

from runner.runner import run_evolution
from visualization.main_window import MainWindow
from PyQt5.QtWidgets import QApplication


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        app = QApplication(sys.argv)
        window = MainWindow(comm)
        window.show()
        app.exec_()
    else:
        while True:
            status = MPI.Status()
            if comm.Iprobe(source=0, tag=MPI.ANY_TAG, status=status):
                msg = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
                if msg == "STOP":
                    break
                if msg == "START":
                    run_evolution(comm, None)
            else:
                time.sleep(0.1)


if __name__ == "__main__":
    main()