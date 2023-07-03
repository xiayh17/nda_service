# NDA Service Application

## Description

此脚本用于从NDA（National Data Archive）服务下载文件。它首先进行身份验证，然后读取manifest文件获取s3文件列表，接着获取每个文件的下载链接，最后下载文件。

## Setting Up

1. 确保您的机器上已安装[Anaconda](https://www.anaconda.com/products/distribution)或[Miniconda](https://docs.conda.io/en/latest/miniconda.html)。

2. 安装[Mamba](https://github.com/mamba-org/mamba)，可以使用以下命令：
    ```bash
    conda install mamba -n base -c conda-forge
    ```

3. 使用Mamba从这个目录运行下列命令以创建和激活conda环境：
    ```bash
    mamba env create -f environment.yml
    conda activate nda_service_env
    ```

4. 复制`.env.sample`为`.env`，然后将您的NDA用户名和密码添加到`.env`文件中。

5. 根据需要修改`config.ini`文件。

## Running the Script

从此目录运行`python nda_service.py`即可开始文件下载。

## License

此项目使用MIT许可证。
