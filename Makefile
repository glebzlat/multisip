PROJECT_SOURCE_DIR = multisip

DESIGN_SOURCE_DIR = ui
DESIGN_OUTPUT_DIR = ${PROJECT_SOURCE_DIR}

DESIGN_INPUT_FILES = $(wildcard ${DESIGN_SOURCE_DIR}/*.ui)
DESIGN_OUTPUT_FILES = $(patsubst %.ui,${DESIGN_OUTPUT_DIR}/%.py,$(DESIGN_INPUT_FILES))

RESOURCES_IN = ${PROJECT_SOURCE_DIR}/resources/resources.qrc
RESOURCES_OUT = ${PROJECT_SOURCE_DIR}/resources.py

all: ${DESIGN_OUTPUT_FILES} ${RESOURCES_OUT}

${DESIGN_OUTPUT_DIR}/ui/%.py: ${DESIGN_SOURCE_DIR}/%.ui
	pyside6-uic $< -o $@
	sed -i 's/resources_rc/multisip.resources/g' $@

${RESOURCES_OUT}: ${RESOURCES_IN}
	pyside6-rcc -g python $< -o $@
