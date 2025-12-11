# Editing Rules

## Function Naming

- **Do NOT rename public functions** unless explicitly asked by the user
- Public functions are those exported in modules and used by CLI commands

## ROI Logic

- **Do NOT remove ROI logic** - it is core to the project
- Only one ROI is used (not multiple)
- ROI selection is interactive in Stage 1
- ROI configuration is stored in `config/roi.yaml`

## Project Structure

- Maintain the structure of the project:
  - `src/smva/` - main package
  - `config/` - configuration files
  - `result/` - output files
  - `docs/` - documentation
  - `.mcp/` - project documentation

## Module Boundaries

- Keep utilities in `utils/` directory
- Stage 1 and Stage 2 are separate modules
- CLI is a thin wrapper around stage functions

## Configuration

- ROI configuration format must remain:
  ```yaml
  roi:
    x: <int>
    y: <int>
    w: <int>
    h: <int>
  video:
    width: <int>
    height: <int>
    fps: <float>
  ```

