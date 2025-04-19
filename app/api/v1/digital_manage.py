# 根路由 
# 功能​：API健康检查端点
@app.get("/")
async def root():
    return {"message": "数字人管理系统API"}

# 数字人管理 
# 功能​：创建新数字人
​# 参数​：DigitalHumanCreate模型（JSON Body）
#      包含音频文件路径字段
​# 响应​：DigitalHumanResponse（含创建结果）
@app.post("/digital-humans/", response_model=DigitalHumanResponse)
async def create_digital_human(...)

# ​功能​：获取数字人列表（支持分页/搜索）
​# 查询参数​：skip: 分页起始位置
#          limit: 每页数量（1-100）
#          search: 搜索关键词
​# 响应​：DigitalHumanListResponse（含分页结果）
@app.get("/digital-humans/", response_model=DigitalHumanListResponse)
async def list_digital_humans(...)

# 功能​：获取单个数字人详情
# ​路径参数​：
# digital_human_id: 数字人ID（支持local-前缀的临时ID）
​# 响应​：DigitalHumanResponse
@app.get("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def get_digital_human(...)

# ​功能​：删除数字人
​# 路径参数​：
# digital_human_id: 数字人ID（支持临时ID）
​# 响应​：操作结果
@app.delete("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def delete_digital_human(...)

# 功能​：更新数字人信息
# ​参数​：
# 路径参数：digital_human_id
# JSON Body更新字段
​# 响应​：更新后的完整数据
@app.put("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def update_digital_human(...)

# 文件上传
# 功能​：上传数字人头像
​# 文件类型​：JPG/PNG
​# 返回​：图片访问URL
@app.post("/upload/image")
async def upload_image(...)

# 功能​：上传参考音频
​# 文件类型​：WAV/MP3
​# 返回​：音频访问URL
@app.post("/upload/reference-audio")
async def upload_reference_audio(...)

# ​功能​：上传训练音频
​# 文件类型​：WAV/MP3
​# 返回​：音频访问URL
@app.post("/upload/training-audio")
async def upload_training_audio(...)
