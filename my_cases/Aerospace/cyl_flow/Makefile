# Makefile for cyl_flow using OpenLB

# Project name
EXAMPLE = cyl_flow

# Path to OpenLB root (relative to this directory)
OLB_ROOT := ../../../olb-release

# Include OpenLB default Makefile
include $(OLB_ROOT)/default.mk

# Custom run target
run:
	@mkdir -p tmp
	@echo "Running $(EXAMPLE)..."
	./$(EXAMPLE)
