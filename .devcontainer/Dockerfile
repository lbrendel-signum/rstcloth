# A useful base repository based on ms devcontainer but with a bunch of fixes
# and useful installs (geo tools are unnecessary for this project, but all the other tweaks are helpful)
FROM windpioneers/gdal-python:little-gecko-gdal-2.4.1-python-3.9-dev

# Tell zsh where you want to store history
#     We leave you to decide, but if you put this into a folder that's been mapped
#     into the container, then history will persist over container rebuilds :)
#
#     !!!IMPORTANT!!!
#     Make sure your .zsh_history file is NOT committed into your repository, as it can contain
#     sensitive information. So in this case, you should add
#         .devcontainer/.zsh_history
#     to your .gitignore file.
#
ENV HISTFILE="/workspaces/rstcloth/.devcontainer/.zsh_history"

# Switch to vscode user
USER vscode
WORKDIR /workspaces/rstcloth

USER vscode
# Install uv
RUN pip install uv

# Install python dependencies using uv
COPY pyproject.toml ./
RUN uv pip install --system --group dev
