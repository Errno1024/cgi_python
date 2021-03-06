import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

github_username = 'Errno1024'
github_project = ''

github_url = f"https://github.com/{github_username}/{github_project}"
setuptools.setup(
    name="cgi_python",
    version="0.0.1",
    author="",
    author_email="",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=github_url,
    project_urls={
        "Bug Tracker": github_url + "/issues",
    },
    classifiers=[],
    packages=setuptools.find_packages(),
)
