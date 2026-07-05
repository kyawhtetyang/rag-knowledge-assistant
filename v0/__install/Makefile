# Automation Makefile for snapshot/restore workflow

PROJECT_ROOT ?= $(abspath ..)
INSTALL_PY ?= $(HOME)/CS/CSO2_AM/01_Install/load/run_install.py

.PHONY: help prepare install-tools open-project snapshot restore roundtrip open-snapshot open-current full group1 group2 group3 group-all

help:
	@echo "Automation commands:"
	@echo "  make group1        # mkdir __install + run_install.py + open project"
	@echo "  make group2        # run_back.py + open all_back.txt"
	@echo "  make group3        # open all.txt + run.py"
	@echo "  make group-all     # group1 -> group2 -> group3"
	@echo "  make prepare       # Ensure __install folder exists under project root"
	@echo "  make install-tools # Run external install bootstrap"
	@echo "  make open-project  # Open project folder"
	@echo "  make snapshot      # Generate __install/all_back.txt from project files"
	@echo "  make restore       # Rebuild project files from __install/all.txt"
	@echo "  make roundtrip     # snapshot -> restore"
	@echo "  make full          # prepare -> install-tools -> snapshot -> open -> restore"
	@echo "  make open-snapshot # Open __install/all_back.txt"
	@echo "  make open-current  # Open __install/all.txt"

prepare:
	mkdir -p "$(PROJECT_ROOT)/__install"

install-tools:
	python "$(INSTALL_PY)"

open-project:
	@open "$(PROJECT_ROOT)"

snapshot:
	python run_back.py

restore:
	python run.py

roundtrip: snapshot restore

open-snapshot:
	open all_back.txt

open-current:
	open all.txt

full: prepare install-tools open-project snapshot open-snapshot open-current restore

prepare: prepare install-tools open-project

all_back: snapshot open-snapshot

all: open-current restore

group-all: prepare all_back all

# ==========================================================
# mkdir -p ~/CS/CSD2_OS/01_File_Organizer/v1/__install
# python ~/CS/CSO2_AM/01_Install/load/run_install.py
# cd ~/CS/CSE4_FE/01_File_Organizer/ && open v1/

# cd ~/CS/CSD2_OS/01_File_Organizer/v1/
# python __install/run_back.py
# open __install/all_back.txt

# cd ~/CS/CSD2_OS/01_File_Organizer/v1/
# open __install/all.txt
# python __install/run.py

