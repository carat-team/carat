# Root justfile. Delegates to per-project justfiles

mod backend
mod algorithms

default:
    @just --list

# Run lint, typecheck and tests for both Python projects
check:
    just algorithms check
    just backend check

# Install dependencies for both Python projects
sync:
    just algorithms sync
    just backend sync
