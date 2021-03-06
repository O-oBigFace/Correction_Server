# # 纠错模块使用说明

[TOC]

---

## 1. 功能说明

本代码实现了**关键词**的自动纠错（错输为拼音的纠正功能），主要功能如下：

1.  根据提供的关键词表构造纠错词表；
2.  给定一个查询句子，根据纠错词表定位并纠正其中的错误。

## 2. 目录结构

本代码目录结构如下：

```bash
-semantic_server # 主目录
	-semantic_server
        -data # 数据存放目录 
            -pkl # pkl格式文件存放，存储AC自动机的pickle文件
            -yml # yml格式文件存放 
                -quesword.yml    #<★疑问词词典>
                -relation.yml    #<★关系词词典>
                -replace.yml     #<替代词词库>
                -wrong_table.yml #<★纠错词典>
                
        -output # 输出数据目录
        	-correction_record # ★纠错模块日志目录
        		-... # 一些日志文件
        	-log # 全部模块(包括崔、徐)的日志文件输出
        		-... # 一些日志文件
        		
        -source # 代码存放目录 
        	-__init__.py
            -intent_extraction #<纠错+意图识别模块>
                -__init__.py
                -actree.py       #<AC自动机的实现代码>
                -dict_builder.py #<构建纠错词典的代码>
                -item_matcher.py  #<★项目接口>
                -recognizer.py   #<AC自动机封装模块>
                -logger.py # 纠错功能日志初始化
                -system_info.py # 记录系统的一些信息
                
        -__init__.py
        -api.py
        -settings.py
        -urls.py
        -wsgi.py
		... # 一些Django功能文件
```

## 3. 项目接口说明

### 3.1 服务调⽤★

-   下⾯的所有操作默认在项⽬根目录下执行，且已经安装Django
-   利⽤用命令开启服务

```python
python manage.py runserver your_ip:port
```

-   向url `http://your_ip:port/correct/`发送⼀一个POST请求，数据包的格式如下:

```json
{"sentence": "问句", "need_correct": true, "account": "账号识别模块的结果"}
```

-   sentence: str, 代表输⼊的问句句
-   need_correct: bool, 代表是否需要纠错，true:需要，false:不需要
-   account: 账号识别模块的结果 (20190709新增)，是一个json值，请直接将**账号识别的输出结果**传入。

### 3.2 接口类

调用接口类为`source.intent_extraction.item_matcher`的类`ItemMatcher`，其中，纠错的接口为`ItemMatcher`的`match(query)`函数。

### 3.3 整体内部调用接口

内部调用接口实现了三个功能：纠错、疑问词识别、关系识别。

#### 3.3.1 示例

```python
from source.intent_extraction.ItemMatcher import ItemMatcher

"""
    类的初始化
    
	new: param
	    布尔变量：True表示重新构建AC自动机，False表示不重新构建
	    new=True建议在首次调用时使用，会根据纠错词典创建AC自动机并保存到本地。
        在后面的调用中，如果new=True会强制重新创建AC自动机。
    
    结论：第一次调用new-True，后面的调用new=False
    
"""
item_matcher = ItemMatcher(new=True)

"""
	整体调用接口
	query: param 
	字符串变量：输入的问句
	
    need_correct: param
    布尔变量：True表示需要调用纠错功能，False表示不调用
    默认值为True
    
    account: 账号识别结果
"""
query = "张三的laopo李四的fuqing是谁"
item_matcher.match(query, need_correct=True, account=account_res)
```

#### 3.3.2 接口说明

`ItemMatcher`类的方法`match(need_correct)`为项目中内部调用接口：

-   参数`query: str`: 输入的问句
-   参数`need_correct: bool`: `True`表示需要调用纠错功能，`False`表示不调用。**默认值为`True`**
-   参数`account`: 表示账号识别模块的结果。

#### 3.3.3 输出格式

输出为json格式，下面为解释：

-   corret_info： dict，包含了所有的纠错信息
    -   correct： list，表中的每个元素都是一个dict，代表了纠错结果的最小单元
        -   begin：int, 错词在**原句**中的开始位置
        -   end：int, 错词在**原句**中的**结束位置的后一位**
        -   type：str, 错词对应的正确词
        -   value：str, 错词的字面值
    -   correct_query: str, 纠正后的问句
-   intent：str，问句的意图，取值范围请看文件*quesword.yml*
-   is_corr：bool, **和调用函数`match(need_correct)`中，变量`need_correct`的值一致，不是句子里有没有错**
-   query：str, 如果问句有错并且被纠正，值为**被纠正后的句子**；否则为**原句**
-   raw_query：str, 原始问句
-   relation：列表，每一个元素代表**关系**识别结果的最小单元
    -   接下来的begin，end，value的对应：如果**问句中有错误并被纠正**，则对应**纠正后句子**；否则对应原句。
    -   begin：int，关系词开始位置
    -   end：int，关系词结束位置的后一位
    -   type：关系词对应了哪种关系，关系词见文件**relation.yml**
    -   value：关系词字面值
    -   code：关系代码 (20190709新增)

##### 示例1：need_correct=True, 且句子中有可以被识别的错误

```json
{
"correct_info": 
    {"correct": 
        [
            {"begin": 8,
             "end": 13,
             "type": "老婆",
             "value": "laopo",
             }
        ],
     "correct_query": "张三的爸爸祖父的老婆是谁",
     },
 "intent": "People",
 "is_corr": true,
 "query": "张三的爸爸祖父的老婆是谁",
 "raw_query": "张三的爸爸祖父的laopo是谁",
 "relation": [{"begin": 3, "end": 5, "type": "Kindred", "code": 2501, "value": "爸爸"},
              {"begin": 5, "end": 7, "type": "Kindred", "code": 2501, "value": "祖父"},
              {"begin": 8, "end": 10, "type": "Kindred", "code": 2501, "value": "老婆"}]}
```

##### 示例2：need_correct=False，且句子中有可以被识别的错误

```json
{'correct_info': None,
 'intent': 'People',
 'is_corr': False,
 'query': '张三的爸爸祖父的laopo是谁',
 'raw_query': '张三的爸爸祖父的laopo是谁',
 'relation': [{'begin': 3, 'end': 5, 'type': 'Kindred', "code": 2501, 'value': '爸爸'},
              {'begin': 5, 'end': 7, 'type': 'Kindred', "code": 2501, 'value': '祖父'}]}
```

##### 示例3：need_correct=True，且句子中没有可以被识别的错误

```json
{'correct_info': {'correct': [], 'correct_query': '张三的爸爸祖父的是谁'},
 'intent': 'People',
 'is_corr': True,
 'query': '张三的爸爸祖父的是谁',
 'raw_query': '张三的爸爸祖父的是谁',
 'relation': [{'begin': 3, 'end': 5, 'type': 'Kindred', "code": 2501, 'value': '爸爸'},
              {'begin': 5, 'end': 7, 'type': 'Kindred', "code": 2501, 'value': '祖父'}]}
```

##### 示例4：need_correct=False，句子无错

和示例3仅仅是 *is_corr*的不同

```json
{'correct_info': None,
 'intent': 'People',
 'is_corr': False,
 'query': '张三的爸爸祖父的是谁',
 'raw_query': '张三的爸爸祖父的是谁',
 'relation': [{'begin': 3, 'end': 5, 'type': 'Kindred', "code": 2501, 'value': '爸爸'},
              {'begin': 5, 'end': 7, 'type': 'Kindred', "code": 2501, 'value': '祖父'}]}
```

### 3.4 纠错功能调用接口

类的初始化方法：

```python
"""
	参数:new=True建议在首次调用时使用，会根据纠错词典创建AC自动机并保存到本地。
        在后面的调用中，如果new=True会强制重新创建AC自动机。
    
    结论：第一次调用new-True，后面的调用new=False
"""
item_matcher = ItemMatcher(new=True)

"""
	纠错函数 correct(query)
	query为查询问句
"""
query = "张三的laopo李四的fuqing是谁"
item_matcher.correct(query)

```

#### 示例

调用示例如下：

```python
from source.intent_extraction.ItemMatcher import ItemMatcher

item_matcher = ItemMatcher(new=True)
query = "张三的laopo李四的fuqing是谁"
print(item_matcher.correct(query))

"""
{'correct': [{'begin': 3, 'end': 8, 'type': '老婆', 'value': 'laopo'},
             {'begin': 11, 'end': 17, 'type': '父亲', 'value': 'fuqing'}],
 'correct_query': '张三的老婆李四的父亲是谁'}
"""

```

---

# # 纠错模块修改说明

## ==修改说明 - 2019年7月17日==

### 说明

#### 1. 修改AC自动机实现上的BUG

该BUG导致了AC自动机的fail指针失效。

>   **现象**
>
>   如果词典中同时包含“在哪儿工作”与“哪上班”，那么查找“在哪儿上班”时会出现未找到的错误。
>
>   **错误原因**
>
>   “在哪上班”包含了前缀“在哪”，由于AC自动机的fail指针失效，当前游标指针不能指向正确的fail结点"根节点->哪"，而依然指向“在哪儿工作的”中的“在->哪”，导致“在哪儿上班无法识别”。

#### ==2. 优化构建纠错词典的算法==

现在纠错功能可以容忍平仄声、大小写、前后鼻音、n和l互换、某些字符的重复。

**目前纠错支持的规则**

1.  某个中文词任意一个位置输入为拼音；

    >   正确词：住在哪儿
    >
    >   错词：zhuzai哪儿、zhuzainaer、住zai哪儿

2.  输入的拼音平仄声不分；

    >   主要是`zh,z |sh,s| ch,c`

3.  拼音前后鼻音不分；

    >   为了更少冲突，只支持`on, ong| en,eng |in, ing`

4.  `n`和`l`不分；

5.  某些拼音字符重复(少数)；

    >   这个如果设置很多会导致词典过大、冲突变多
    >   laopo 和 laopoo

6.  某些错别字(少数)；

    >   “哪”和“那”
    >
    >   ”妈“和”麻“

7.  拼音大小写不分；

**具体纠错的字符替换规则可以查看`replace.yml`，内有注释。**

### 文件更改

```bash
-semantic_server # 主目录
	-semantic_server
        -data # 数据存放目录 
            -yml # yml格式文件存放 
                -relation.yml    #<关系词词典> 	☆更改
                -wrong_table.yml #<纠错词典>	☆更改
        -source # 代码存放目录 
        	-__init__.py
            -intent_extraction #<纠错+意图识别模块>		☆更改，直接替换目录即可
                -__init__.py
                -actree.py       #<AC自动机的实现代码>	☆更改
                -dict_builder.py #<构建纠错词典的代码>	☆更改
                -item_matcher.py  #<★项目接口>			☆更改
                -recognizer.py   #<AC自动机封装模块>	☆更改
                -logger.py # 纠错功能日志初始化
                -system_info.py # 记录系统的一些信息
                
```



---

## 修改说明 - 2019年7月9日

### 说明

#### 1. 纠错功能访问地址更改

为了使访问地址和总体项目保持一致，先将Django纠错模块的访问地址由`http://your_ip:port/correct`改变为`http://your_ip:port/correct/`；

因此下图的问题得到了解决，**==路径后面都要加`/`==**.

![image-20190629125849079](../../%E7%83%BD%E7%81%AB%E6%98%9F%E7%A9%BA/%E5%AE%9E%E7%8E%B0/assets/image-20190629125849079.png)

#### 2. 修复了将账号文本识别为拼音的问题(目前只能在整体流程中测试)

因为账号识别依然属于NER模块，所以单独的纠错模块无法直接调用账号识别结果。

但是，账号识别的接口已经开放，可以手动将账号识别的结果加入到项目接口中，详情见**3.1 服务调用**。

#### 3. 新增了关系代码

依据本体中的关系代码加入到了最终输出结果中，详情见**3.3.3 输出格式**

### 文件更改

```bash
-semantic_server # 主目录
	-semantic_server
        -data # 数据存放目录 
            -yml # yml格式文件存放 
            	-relation_code.yml #<关系代码>	★新增
                -relation.yml    #<关系词词典> 	☆更改
                -wrong_table.yml #<纠错词典>	☆更改
        -source # 代码存放目录 
        	-__init__.py
            -intent_extraction #<纠错+意图识别模块>		☆更改，直接替换目录即可
                -__init__.py
                -actree.py       #<AC自动机的实现代码>
                -dict_builder.py #<构建纠错词典的代码>	
                -item_matcher.py  #<★项目接口>
                -recognizer.py   #<AC自动机封装模块>
                -logger.py # 纠错功能日志初始化
                -system_info.py # 记录系统的一些信息
                
        -__init__.py
        -urls.py	# Django☆更改
		-api.py # 一些Django功能文件	☆更改
```



------

## 修改说明 - 2019年6月27日

### 说明

1.  增加了大写字母识别功能；
2.  扩充了关系词词库，添加了"爷爷“、”奶奶"、“外公”、“外婆”等关系；

### 仍存在问题

-   将账号中的拼音错误识别为关系，这部分需要账号识别与纠错模块联动。需要后期设计规则规避此问题。

### 文件更改

涉及到的文件更改如下：

```bash
-semantic_server # 主目录
	-semantic_server
        -data # 数据存放目录 
            -yml # yml格式文件存放 
                -relation.yml    #<关系词词典> 	☆更改
                -wrong_table.yml #<纠错词典>	☆更改
				...
        -source # 代码存放目录 
            -intent_extraction #<纠错+意图识别模块>
                -item_matcher.py  #<项目接口>	☆更改
				...

```