## 安装&&升级

###  打包流程

#### 安装依赖

```shell
# 进入虚拟环境
pip3 install -r requirements.txt
```

#### 填写配置文件

- package_name：包名，打包之后生成的压缩包的名字
- package_type： 当前安装包的类型(package_type), 可选值为 constant.PackageTypeEnum中的值
  - install_rdb_server：安装rdb server
  - install_rdb_worker：安装rdb worker
  - install_rdb_agent：安装rdb agent
  - install_update_code：代码patch包
  - install_update_agent：agent工具patch包
- os_release：Linux发行版本(centos|bclinux)，同时支持多个配置用英文逗号隔开，
  - 从操作系统中查看`cat /etc/os-release ` 其中`ID="centos"`

```shell
cat version.json

{
    "package_name": "update_code_5.7.1.0_centos.x86_64",
    "package_type": "install_update_code",
    "os_release": "bclinux,centos",
    "_os_release": "当前安装包的操作系统版本(os_release), 多个值中间用英文逗号分隔",
    "_package_type": "当前安装包的类型(package_type), 可选值为 constant.PackageTypeEnum中的值"
}
```

#### 准备好package.tar.gz

1. rdb server初始化安装包

   ```shell
   tar -tf package.tar.gz
   .
   └── aio-5.7.1.0-1_1.el7.x86_64.rpm
   ```

2. rdb worker初始化安装包

   ```shell
   tar -tf package.tar.gz
   .
   └── aio-airflow-5.7.1.0-1_1.el7.x86_64.rpm
   ```

3. rdb agent初始化安装包

   ```shell
   tar -tf package.tar.gz
   .
   ├── fsbackup_kernel_4.x
   └── tools
   ```

4. rdb agent升级包

   ```shell
   tar -tf package.tar.gz
   .
   ├── fsbackup_kernel_4.x
   └── tools
   ```

5. rdb code升级包

   ```shell
   tar -tf package.tar.gz
   ├── aio-5.5.1.0-py3-none-any.whl
   ├── aio_public_module-1.0-py3-none-any.whl
   ├── aio_tasks-5.5.1.0rc1.dev149+g44dce80.d20250814-py3-none-any.whl
   ├── tasks-5.5.1.0rc1.dev149+g44dce80.d20250814-py3-none-any.whl
   └── tools
   ```

#### 运行打包命令

```shell
python3 build.py
```

### 安装流程

#### 解压安装包

```shell
tar -zxvf rdb_server_5.7.1.0_centos.x86_64.tar.gz
```

#### 执行安装命令

```shell
cd rdb_worker_5.7.1.0_centos.x86_64
./install
```

#### 特殊处理

```shell
./install --help

usage: install [-h] [-f]

tools installer or updater

optional arguments:
  -h, --help   show this help message and exit
  -f, --force  force install or update
```

1. 在agent安装包和升级包中，执行安装命令的时候，支持强制安装

   1. `./install` :普通安装，查询工具集相关后台服务在运行中时，退出安装流程，需要手动关闭后台进程，然后再重新安装
   2. `./install -f`: 强制安装，程序会关闭后台进程之后，自动进入安装流程。
