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
async def create_digital_human(
    request: Request,
    digital_human: DigitalHumanCreate,
    db: DatabaseManager = Depends(get_db)
):
    """
    创建新的数字人
    """
    # 记录原始请求体，以检查路径字段
    body = await request.body()
    try:
        raw_data = json.loads(body)
        logger.info(f"收到原始请求数据: {raw_data}")
    except:
        logger.info(f"无法解析原始请求数据: {body}")
        
    digital_human_data = digital_human.model_dump(exclude_unset=True)
    logger.info(f"Pydantic模型解析后的数据: {digital_human_data}")
    
    # 确保必要字段存在，如果不存在则设置默认值
    _ensure_required_fields(digital_human_data)
    logger.info(f"添加默认值后的数据: {digital_human_data}")
    
    # avatar字段现在应该是从/upload/image接口获取的URL，无需再处理文件
    # 只需处理音频文件路径
    if 'original_reference_audio_path' in digital_human_data and digital_human_data['original_reference_audio_path']:
        logger.info(f"处理参考音频文件: {digital_human_data['original_reference_audio_path']}")
        reference_audio_url = copy_file_to_static(digital_human_data['original_reference_audio_path'], AUDIO_DIR)
        if reference_audio_url:
            digital_human_data['referenceAudio'] = reference_audio_url
    
    if 'original_training_audio_path' in digital_human_data and digital_human_data['original_training_audio_path']:
        logger.info(f"处理训练音频文件: {digital_human_data['original_training_audio_path']}")
        training_audio_url = copy_file_to_static(digital_human_data['original_training_audio_path'], AUDIO_DIR)
        if training_audio_url:
            digital_human_data['trainingAudio'] = training_audio_url
    
    try:
        # 调用数据库方法添加数字人
        logger.info(f"准备添加到数据库的数据: {digital_human_data}")
        new_id = db.add_digital_human(digital_human_data)
        logger.info(f"数据库返回的ID: {new_id}")
        
        if not new_id:
            logger.warning("数据库未返回ID，创建本地数据")
            # 如果数据库操作失败，创建一个本地临时ID
            local_id = f"local-{int(time.time() * 1000)}"
            digital_human_data['id'] = local_id
            LOCAL_TEMP_DATA[local_id] = digital_human_data
            
            return DigitalHumanResponse(
                success=True,  # 即使是本地创建，也返回成功
                message="创建数字人成功（本地模式）",
                data=DigitalHuman(**digital_human_data)
            )
        
        # 获取创建的数字人数据
        created_human = db.get_digital_human(new_id)
        logger.info(f"从数据库获取的创建结果: {created_human}")
        
        # 确保所有必要字段存在，不存在则设置默认值
        if created_human:
            _ensure_required_fields(created_human)
            logger.info(f"最终返回的数据: {created_human}")
        else:
            logger.error(f"无法从数据库获取刚创建的数字人 ID: {new_id}")
        
        return DigitalHumanResponse(
            success=True,
            message="创建数字人成功",
            data=DigitalHuman(**created_human)
        )
    except Exception as e:
        # 捕获异常，确保即使出错也能返回一个有效的响应
        logger.error(f"创建数字人出错: {e}", exc_info=True)
        
        # 创建一个本地临时ID
        local_id = f"local-{int(time.time() * 1000)}"
        digital_human_data['id'] = local_id
        LOCAL_TEMP_DATA[local_id] = digital_human_data
        
        return DigitalHumanResponse(
            success=True,  # 即使是本地创建，也返回成功
            message="创建数字人成功（本地模式）",
            data=DigitalHuman(**digital_human_data)
        )



# ​功能​：获取数字人列表（支持分页/搜索）
​# 查询参数​：skip: 分页起始位置
#          limit: 每页数量（1-100）
#          search: 搜索关键词
​# 响应​：DigitalHumanListResponse（含分页结果）
@app.get("/digital-humans/", response_model=DigitalHumanListResponse)
async def list_digital_humans(
    skip: int = Query(0, ge=0, description="分页起始位置"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: DatabaseManager = Depends(get_db)
):
    """
    获取数字人列表，支持分页和搜索
    """
    try:
        if search:
            # 使用搜索功能
            humans, total = db.search_digital_humans(search, skip, limit)
        else:
            # 使用分页功能
            humans, total = db.get_digital_humans_with_pagination(skip, limit)
        
        logger.info(f"从数据库获取的数据: {humans}")
        
        # 确保每条记录都有必要的字段
        for human in humans:
            _ensure_required_fields(human)
        
        logger.info(f"添加默认值后的数据: {humans}")
        
        # 添加临时创建的本地数据（如果有）
        local_humans = list(LOCAL_TEMP_DATA.values())
        if local_humans and not search:  # 在搜索模式下不添加本地数据
            total += len(local_humans)
            if skip < len(local_humans):
                # 只添加在当前分页范围内的本地数据
                local_to_add = local_humans[skip:skip+limit]
                humans = local_to_add + humans
                if len(humans) > limit:
                    humans = humans[:limit]
        
        return DigitalHumanListResponse(
            success=True,
            message="获取数字人列表成功",
            data=DigitalHumanList(
                items=[DigitalHuman(**human) for human in humans],
                total=total
            )
        )
    except Exception as e:
        logger.error(f"获取数字人列表出错: {e}", exc_info=True)
        # 返回本地数据作为备份
        local_humans = list(LOCAL_TEMP_DATA.values())
        
        return DigitalHumanListResponse(
            success=True,
            message="获取数字人列表成功（本地模式）",
            data=DigitalHumanList(
                items=[DigitalHuman(**human) for human in local_humans],
                total=len(local_humans)
            )
        )



# 功能​：获取单个数字人详情
# ​路径参数​：
# digital_human_id: 数字人ID（支持local-前缀的临时ID）
​# 响应​：DigitalHumanResponse
@app.get("/digital-humans/{digital_human_id}", response_model=DigitalHumanResponse)
async def get_digital_human(
    digital_human_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    获取指定ID的数字人
    """
    logger.info(f"获取数字人 ID: {digital_human_id}")
    
    # 检查是否是本地临时ID
    if digital_human_id.startswith("local-") and digital_human_id in LOCAL_TEMP_DATA:
        local_data = LOCAL_TEMP_DATA[digital_human_id]
        _ensure_required_fields(local_data)
        logger.info(f"从本地存储获取的数据: {local_data}")
        
        return DigitalHumanResponse(
            success=True,
            message="获取数字人成功（本地模式）",
            data=DigitalHuman(**local_data)
        )
    
    try:
        # 尝试从数据库获取
        human = db.get_digital_human(int(digital_human_id))
        logger.info(f"从数据库获取的数据: {human}")
        
        if not human:
            logger.warning(f"数据库中不存在ID为{digital_human_id}的数字人")
            return DigitalHumanResponse(
                success=False,
                message=f"ID为{digital_human_id}的数字人不存在"
            )
        
        # 确保所有必要字段存在
        _ensure_required_fields(human)
        logger.info(f"添加默认值后的数据: {human}")
        
        return DigitalHumanResponse(
            success=True,
            message="获取数字人成功",
            data=DigitalHuman(**human)
        )
    except ValueError:
        # 如果ID不是整数也不是有效的本地ID
        logger.error(f"无效的ID格式: {digital_human_id}")
        return DigitalHumanResponse(
            success=False,
            message=f"无效的ID格式: {digital_human_id}"
        )
    except Exception as e:
        logger.error(f"获取数字人信息出错: {e}", exc_info=True)
        return DigitalHumanResponse(
            success=False,
            message=f"获取数字人信息时发生错误"
        )



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
