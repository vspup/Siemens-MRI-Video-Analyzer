# Project Rules

## Language

- **Project language**: English
- **User communication**: User may communicate in Russian
- **Code comments**: Must be in English
- **Documentation**: Must be in English
- **Filenames**: Must be in English

## Project Philosophy

- Keep the project simple and extendable
- Focus on the core functionality: ROI selection and OCR processing
- Maintain clear separation between stages
- Use standard Python libraries and well-established packages

## Constraints

- Only ONE ROI rectangle is used (not multiple ROIs)
- ROI must contain all four data lines
- Frames with current_A > 550 are automatically skipped
- Output format is fixed JSON structure

