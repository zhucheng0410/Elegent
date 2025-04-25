import git
from multiprocessing import Process,Queue
import os
import shutil
from concurrent.futures import ThreadPoolExecutor



"""
    从html_url.txt文件里拿出项目url 然后添加到 q1 队列里
"""
def html_url_get(q1):
    with open("myhtml_url.txt",'r',encoding='utf-8') as f:
        file_list = f.readlines()
    for fi in file_list:
        path = fi.split('\t')[0]
        q1.put(path)
"""
    连接仓库
    从q1 中拿到GitHub项目url ,将连接成功的路径path 传递到 q2 队列中     q2.put(path)
"""
def connect_git(q1,q2):
    #使用 线程池 增快拉取速度
    with ThreadPoolExecutor(25) as p:
        while True:
            try:
                ht_url = q1.get(timeout=3600)
            except:
                break
            p.submit(fun1,ht_url,q2)
"""
    连接GitHub远程仓库函数
"""
def fun1(ht_url,q2):
    name = ht_url.split('/')
    path = "D:\\实验室项目\\github数据\\{}".format(name[-2] + '&' + name[-1]+"&blob&master")
    html_url = "git@github.com:" + name[-2] + "/" + name[-1] + '.git'
    a = 0
    # 尝试连接，报错后重新连接
    while True:
        try:
            git.Repo.clone_from(html_url, to_path=path, depth=1, filter="blob:none", no_checkout=True)
            break
        except git.exc.GitCommandError:
            a += 1
            if a == 6:
                break
            if os.path.exists(path):
                shutil.rmtree(path)
            continue
    q2.put(path)
"""
    对连接好的仓库，进行拉取需要的代码文件
    利用 q2 中的路径 path 进行拉取，将拉取成功的路径path 传递到q3中    q3.put(path)
"""
def pulling_git(q2,q3):
    with ThreadPoolExecutor(25) as p:
        while True:
            try:
                path = q2.get(timeout=3600)
            except:
                break
            p.submit(fun2,path,q3)
"""
    对连接好的仓库，进行拉取需要的代码文件的函数
"""
def fun2(path, q3):
    try:
        repo = git.Repo(path)
        sparse_checkout = repo.config_writer()
        sparse_checkout.set_value('core', 'sparsecheckout', 'true')
        sparse_checkout.release()
        write_list = ["*.php", "*.cs", "*.go", "*.rb","*.swift","*.m","*.mm","*.erl","*.groovy","*.scala","*.pl","*.pm","*.r","*.rs","*.clj","*.kt","*.kts","*.dart","*.sql","*.c","*.cpp","*.java","*.py"]
        with open(repo.working_tree_dir + '\\.git\\info\\sparse-checkout', 'w') as fi:
            for write in write_list:
                fi.write('{}\n'.format(write))
        try:
            repo.git.checkout()  # 解决不了出现 invalid path 的报错，可以先跳过
            q3.put(path)
        except:
            pass
    except:
        print(path,"报错")
        return
"""
    将本地仓库里的代码文件 按照 不同后缀（即不同代码文件）移动到特定的文件夹下   （即所有.py 文件移动到 py文件夹下）
"""
def move_file(q3):
    with ThreadPoolExecutor(25) as p:
        while True:
            try:
                local_path = q3.get(timeout=3600)
            except:
                break
            p.submit(list_files,local_path)
            print(local_path)
"""
   移动代码文件的实现函数 
"""
def list_files(folder_path):
    # 遍历文件夹
    dst_path = "D:\\实验室项目\\6.8-9.12\\"
    """
        这是看我们具体需要那些代码文件
    """
    file_type = ["php", "cs", "go", "rb","swift","m","mm","erl","groovy","scala","pl","pm","r","rs","clj","kt","kts","dart","sql","c","cpp","java","py"]
    for file_name in os.listdir(folder_path):
        # if file_name == ".git":
        #     shutil.rmtree(os.path.join(folder_path, file_name), ignore_errors=True)
        #     continue
        # 获取文件完整路径
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):  # 判断是否为文件
            f_name = file_name.split('.')[-1]
            for f_type in file_type:
                if f_name == f_type:
                    new_name = folder_path.replace('\\','&')[18:]+'&'+file_name
                    os.rename(folder_path+"\\"+file_name,folder_path+"\\"+new_name)
                    file_path = os.path.join(folder_path,new_name)
                    shutil.move(file_path, dst_path+f_type)
        elif os.path.isdir(file_path):  # 判断是否为文件夹
            # 如果是文件夹，则递归调用该函数来继续遍历子文件夹
            list_files(file_path)
            shutil.rmtree(file_path, ignore_errors=True)


if __name__ == '__main__':

    """
        这是看我们具体需要那些代码文件
    """
    file_type = ["php", "cs", "go", "rb","swift","m","mm","erl","groovy","scala","pl","pm","r","rs","clj","kt","kts","dart","sql","c","cpp","java","py"]
    for file in file_type:
        if not os.path.exists("D:\\实验室项目\\6.8-9.12\\{}".format(file)):
            os.makedirs("D:\\实验室项目\\6.8-9.12\\{}".format(file))

    """
        利用多进程来提高速度
    """
    q1 = Queue()
    q2 = Queue()
    q3 = Queue()
    # q4 = Queue()
    p1 = Process(target=html_url_get, args=(q1,))
    p2 = Process(target=connect_git, args=(q1,q2,))
    # p4 = Process(target=connect_git, args=(q1,q2,))
    p3 = Process(target=pulling_git, args=(q2, q3,))
    # p5 = Process(target=pulling_git, args=(q2,q3,))
    p6 = Process(target=move_file,args=(q3,))
    # p7 = Process(target=move_file, args=(q3,))
    p1.start()
    p2.start()
    p3.start()
    # p4.start()
    # p5.start()
    p6.start()
    # p7.start()
    p1.join()
    p2.join()
    p3.join()
    # p4.join()
    # p5.join()
    p6.join()
    # p7.join()