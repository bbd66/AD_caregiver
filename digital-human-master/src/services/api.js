// API基础URL，可根据环境配置更改
const API_BASE_URL = 'http://localhost:8000'; // 替换为您的实际API地址

// API路径前缀
const DIGITAL_API_PREFIX = '/api/v1/digital';
const FILES_API_PREFIX = '/api/v1/files';
const VOICE_API_PREFIX = '/api/v1/voice';

// 导入 lamejs 库
let Mp3Encoder;
try {
  import('lamejs').then(module => {
    Mp3Encoder = module.Mp3Encoder;
  }).catch(error => {
    console.error('Failed to load lamejs:', error);
  });
} catch (error) {
  console.error('Error importing lamejs:', error);
}

/**
 * 数字人API服务
 */
const digitalHumanService = {
  /**
   * 获取数字人列表
   * @param {Object} params - 查询参数
   * @param {number} params.skip - 分页起始位置
   * @param {number} params.limit - 每页数量
   * @param {string} params.search - 搜索关键词(可选)
   * @returns {Promise} - 返回数字人列表数据
   */
  getDigitalHumans: async (params = { skip: 0, limit: 10, search: null }) => {
    try {
      let url = `${API_BASE_URL}${DIGITAL_API_PREFIX}/digital-humans/?skip=${params.skip}&limit=${params.limit}`;
      if (params.search) {
        url += `&search=${encodeURIComponent(params.search)}`;
      }
      
      const response = await uni.request({
        url,
        method: 'GET',
        header: {
          'Content-Type': 'application/json'
        }
      });
      
      // uni.request在成功时返回的是一个包含data和statusCode的对象
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.data;
      } else {
        throw new Error(`请求失败: ${response.statusCode}`);
      }
    } catch (error) {
      console.error('获取数字人列表失败:', error);
      throw error;
    }
  },
  
  /**
   * 获取单个数字人详情
   * @param {number} id - 数字人ID
   * @returns {Promise} - 返回数字人详情数据
   */
  getDigitalHuman: async (id) => {
    try {
      const response = await uni.request({
        url: `${API_BASE_URL}${DIGITAL_API_PREFIX}/digital-humans/${id}`,
        method: 'GET',
        header: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.data;
      } else {
        throw new Error(`请求失败: ${response.statusCode}`);
      }
    } catch (error) {
      console.error(`获取数字人(ID:${id})详情失败:`, error);
      throw error;
    }
  },
  
  /**
   * 创建数字人
   * @param {Object} digitalHuman - 数字人数据
   * @returns {Promise} - 返回创建结果
   */
  createDigitalHuman: async (digitalHuman) => {
    try {
      // 添加调试日志
      console.log("创建数字人，传入数据:", digitalHuman);
      
      // 转换字段以匹配后端期望的格式
      const transformedData = {
        name: digitalHuman.name,
        phone: digitalHuman.phone,
        description: digitalHuman.description,
        image_path: digitalHuman.avatar, // 从 avatar 映射到 image_path
        train_audio_path: digitalHuman.trainingAudio, // 从 trainingAudio 映射到 train_audio_path
        reference_audio_path: digitalHuman.referenceAudio, // 从 referenceAudio 映射到 reference_audio_path
        user_id: digitalHuman.user_id || 1 // 添加用户ID字段，默认为1
      };
      
      console.log("转换后发送到后端的数据:", transformedData);
      console.log("请求URL:", `${API_BASE_URL}${DIGITAL_API_PREFIX}/digital-humans/`);
      
      // 添加更多错误处理的uni.request调用
      return new Promise((resolve, reject) => {
        uni.request({
          url: `${API_BASE_URL}${DIGITAL_API_PREFIX}/digital-humans/`,
          method: 'POST',
          header: {
            'Content-Type': 'application/json'
          },
          data: transformedData,
          success: (response) => {
            console.log("API响应成功:", response);
            // 检查响应状态码
            if (response.statusCode >= 200 && response.statusCode < 300) {
              resolve(response.data);
            } else {
              const errorMsg = `请求失败: ${response.statusCode}`;
              console.error(errorMsg, response);
              // 即使API返回了错误状态码，也返回响应数据
              resolve({
                success: false,
                statusCode: response.statusCode,
                message: errorMsg,
                data: response.data
              });
            }
          },
          fail: (error) => {
            console.error("API请求失败:", error);
            
            // 检查网络连接
            uni.getNetworkType({
              success: (networkState) => {
                console.log("网络状态:", networkState);
                
                // 尝试CORS诊断
                if (error.errMsg && error.errMsg.includes("request:fail")) {
                  console.log("可能遇到CORS问题，请确认后端服务器已添加CORS头");
                }
              }
            });
            
            // 创建一个带有更多信息的响应对象
            resolve({
              success: false,
              message: error.errMsg || '网络请求失败',
              errorType: 'REQUEST_FAILED',
              originalError: error
            });
          }
        });
      });
    } catch (error) {
      console.error('创建数字人失败:', error);
      // 返回一个格式化的错误响应
      return {
        success: false,
        message: error.message || '处理请求时出错',
        errorType: 'PROCESSING_ERROR',
        originalError: error
      };
    }
  },
  
  /**
   * 删除数字人
   * @param {number} id - 数字人ID
   * @returns {Promise} - 返回删除结果
   */
  deleteDigitalHuman: async (id) => {
    try {
      const response = await uni.request({
        url: `${API_BASE_URL}${DIGITAL_API_PREFIX}/digital-humans/${id}`,
        method: 'DELETE',
        header: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.data;
      } else {
        throw new Error(`请求失败: ${response.statusCode}`);
      }
    } catch (error) {
      console.error(`删除数字人(ID:${id})失败:`, error);
      throw error;
    }
  },
  
  /**
   * 训练数字人声音
   * @param {number} id - 数字人ID
   * @param {string} audioUrl - 训练音频URL
   * @param {string} customName - 自定义名称，默认使用数字人ID
   * @param {string} model - 使用的模型，默认为"FunAudioLLM/CosyVoice2-0.5B"
   * @returns {Promise} - 返回训练任务提交结果
   */
  trainDigitalHuman: async (id, audioUrl, customName = null, model = "FunAudioLLM/CosyVoice2-0.5B") => {
    try {
      console.log("开始训练数字人:", id, "音频URL:", audioUrl);
      
      // 构建请求数据
      const requestData = {
        dh_id: id.toString(), // 确保ID为字符串类型
        audio_url: audioUrl,
        custom_name: customName || `DigitalHuman_${id}`, // 如果未提供自定义名称，使用默认格式
        model: model, // 使用默认模型或传入的模型
        text: "您好，我是您的智能数字人助手，很高兴为您服务。" // 默认训练文本
      };
      
      console.log("训练请求数据:", requestData);
      
      const response = await uni.request({
        url: `${API_BASE_URL}${VOICE_API_PREFIX}/train/${id}`,
        method: 'POST',
        header: {
          'Content-Type': 'application/json'
        },
        data: requestData
      });
      
      console.log("训练响应:", response);
      
      // 检查响应状态码
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return {
          success: true,
          message: '训练任务已提交',
          data: response.data
        };
      } else {
        return {
          success: false,
          message: `训练任务提交失败: ${response.statusCode}`,
          data: response.data
        };
      }
    } catch (error) {
      console.error("训练数字人失败:", error);
      return {
        success: false,
        message: error.message || '网络请求失败',
        error: error
      };
    }
  },
  
  /**
   * 获取数字人训练状态
   * @param {number} id - 数字人ID
   * @returns {Promise} - 返回训练状态
   */
  getTrainingStatus: async (id) => {
    try {
      const response = await uni.request({
        url: `${API_BASE_URL}${VOICE_API_PREFIX}/train/status/${id}`,
        method: 'GET',
        header: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return {
          success: true,
          data: response.data,
          status: response.data.status || 'unknown'
        };
      } else {
        return {
          success: false,
          message: `获取训练状态失败: ${response.statusCode}`,
          status: 'unknown'
        };
      }
    } catch (error) {
      console.error(`获取数字人(ID:${id})训练状态失败:`, error);
      return {
        success: false,
        message: error.message || '网络请求失败',
        status: 'unknown'
      };
    }
  },
  
  /**
   * 生成数字人语音
   * @param {number} id - 数字人ID
   * @param {string} audioUrl - 要转换的音频URL或文本内容
   * @returns {Promise} - 返回生成的语音音频URL
   */
  generateVoice: async (id, audioUrl) => {
    try {
      console.log("开始生成数字人语音:", id, "输入:", audioUrl);
      
      const response = await uni.request({
        url: `${API_BASE_URL}${VOICE_API_PREFIX}/generate/${id}`,
        method: 'POST',
        header: {
          'Content-Type': 'application/json'
        },
        data: {
          dh_id: id.toString(),
          audio_url: audioUrl
        }
      });
      
      console.log("语音生成响应:", response);
      
      // 检查响应状态码
      if (response.statusCode >= 200 && response.statusCode < 300) {
        // 提取生成的音频URL
        const audioUrl = response.data.audio_url;
        
        // 确保返回完整URL
        const fullAudioUrl = audioUrl.startsWith('http') 
          ? audioUrl 
          : `${API_BASE_URL}${audioUrl.startsWith('/') ? '' : '/'}${audioUrl}`;
          
        return {
          success: true,
          message: '语音生成成功',
          audioUrl: fullAudioUrl,
          duration: response.data.duration || 0
        };
      } else {
        return {
          success: false,
          message: `语音生成失败: ${response.statusCode}`,
          data: response.data
        };
      }
    } catch (error) {
      console.error("生成数字人语音失败:", error);
      return {
        success: false,
        message: error.message || '网络请求失败',
        error: error
      };
    }
  }
};

/**
 * 文件上传API服务
 */
const fileUploadService = {
  /**
   * 上传图片
   * @param {string} filePath - 本地图片路径
   * @returns {Promise<string>} - 返回上传后的图片URL
   */
  uploadImage: (filePath) => {
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${API_BASE_URL}${FILES_API_PREFIX}/upload/image`,
        filePath: filePath,
        name: 'file',
        success: (uploadRes) => {
          try {
            console.log('上传响应:', uploadRes);
            if (uploadRes.statusCode === 200) {
              const data = JSON.parse(uploadRes.data);
              if (data.success && data.imageUrl) {
                // 需要拼接完整URL，因为后端返回的是相对路径
                const fullImageUrl = `${API_BASE_URL}${data.imageUrl}`;
                resolve(fullImageUrl);
              } else {
                reject(new Error(data.message || '上传失败'));
              }
            } else {
              reject(new Error(`请求失败，状态码: ${uploadRes.statusCode}`));
            }
          } catch (e) {
            console.error('解析响应失败:', e, uploadRes);
            reject(new Error('解析响应失败'));
          }
        },
        fail: (err) => {
          console.error('上传请求失败:', err);
          reject(err);
        }
      });
    });
  },
  
  /**
   * 上传训练音频
   * @param {string} filePath - 本地音频文件路径
   * @returns {Promise<string>} - 返回上传后的音频URL
   */
  uploadTrainingAudio: (filePath) => {
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${API_BASE_URL}${FILES_API_PREFIX}/upload/training-audio`,
        filePath: filePath,
        name: 'file',
        success: (uploadRes) => {
          try {
            console.log('上传响应:', uploadRes);
            if (uploadRes.statusCode === 200) {
              const data = JSON.parse(uploadRes.data);
              if (data.success && data.audioUrl) {
                // 需要拼接完整URL，因为后端返回的是相对路径
                const fullAudioUrl = `${API_BASE_URL}${data.audioUrl}`;
                resolve(fullAudioUrl);
              } else {
                reject(new Error(data.message || '上传失败'));
              }
            } else {
              reject(new Error(`请求失败，状态码: ${uploadRes.statusCode}`));
            }
          } catch (e) {
            console.error('解析响应失败:', e, uploadRes);
            reject(new Error('解析响应失败'));
          }
        },
        fail: (err) => {
          console.error('上传请求失败:', err);
          reject(err);
        }
      });
    });
  },
  
  /**
   * 上传参考音频
   * @param {string} filePath - 本地音频文件路径
   * @returns {Promise<string>} - 返回上传后的音频URL
   */
  uploadReferenceAudio: (filePath) => {
    return new Promise((resolve, reject) => {
      uni.uploadFile({
        url: `${API_BASE_URL}${FILES_API_PREFIX}/upload/reference-audio`,
        filePath: filePath,
        name: 'file',
        success: (uploadRes) => {
          try {
            console.log('上传响应:', uploadRes);
            if (uploadRes.statusCode === 200) {
              const data = JSON.parse(uploadRes.data);
              if (data.success && data.audioUrl) {
                // 需要拼接完整URL，因为后端返回的是相对路径
                const fullAudioUrl = `${API_BASE_URL}${data.audioUrl}`;
                resolve(fullAudioUrl);
              } else {
                reject(new Error(data.message || '上传失败'));
              }
            } else {
              reject(new Error(`请求失败，状态码: ${uploadRes.statusCode}`));
            }
          } catch (e) {
            console.error('解析响应失败:', e, uploadRes);
            reject(new Error('解析响应失败'));
          }
        },
        fail: (err) => {
          console.error('上传请求失败:', err);
          reject(err);
        }
      });
    });
  },

  // 验证音频文件格式
  validateAudioFormat: (file) => {
    const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm'];
    if (!validTypes.includes(file.type)) {
      throw new Error(`不支持的音频格式: ${file.type}。支持的格式: WAV, MP3`);
    }
    console.log('音频格式验证通过:', file.type);
    return true;
  },

  // 上传录音音频
  uploadRecordedAudio: async (file) => {
    console.log('开始上传录音音频:', file);
    
    try {
      // 验证文件格式
      fileUploadService.validateAudioFormat(file);
      
      let audioBlob;
      // 如果是 WebM 格式，需要转换为 WAV
      if (file.type === 'audio/webm') {
        console.log('检测到 WebM 格式，开始转换为 WAV...');
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await file.arrayBuffer();
        console.log('音频数据已读取，大小:', arrayBuffer.byteLength);
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        console.log('音频数据已解码，采样率:', audioBuffer.sampleRate);
        const wavBlob = convertToWav(audioBuffer);
        console.log('WAV 转换完成，大小:', wavBlob.size);
        audioBlob = wavBlob;
      } else {
        audioBlob = file;
      }

      // 创建新的 File 对象
      const convertedFile = new File(
        [audioBlob],
        file.name.replace('.webm', '.wav'),
        { type: 'audio/wav' }
      );
      console.log('准备上传文件:', convertedFile);

      // 创建 FormData
      const formData = new FormData();
      formData.append('file', convertedFile);

      // 使用 fetch API 上传
      const response = await fetch(`${API_BASE_URL}${FILES_API_PREFIX}/upload/recorded-audio`, {
        method: 'POST',
        body: formData
      });

      console.log('录音上传响应:', response.status);
      const responseData = await response.json();
      
      if (response.ok && responseData.success) {
        return {
          success: true,
          audioUrl: responseData.audioUrl.startsWith('http') 
            ? responseData.audioUrl 
            : `${API_BASE_URL}${responseData.audioUrl}`
        };
      } else {
        throw new Error(responseData.message || '录音上传失败');
      }
    } catch (error) {
      console.error('处理录音文件失败:', error);
      throw error;
    }
  }
};

// 将音频转换为标准 MP3 格式
const convertToMp3 = async (file) => {
  return new Promise((resolve, reject) => {
    try {
      if (!Mp3Encoder) {
        throw new Error('Mp3Encoder is not available. Make sure lamejs is properly installed.');
      }
      
      // 创建音频上下文
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // 读取文件为 ArrayBuffer
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          // 解码音频数据
          const audioBuffer = await audioContext.decodeAudioData(e.target.result);
          
          // 创建 MP3 编码器
          const mp3encoder = new Mp3Encoder(1, audioBuffer.sampleRate, 128);
          
          // 获取音频数据
          const samples = audioBuffer.getChannelData(0);
          const sampleBlockSize = 1152;
          const mp3Data = [];
          
          // 分块编码
          for (let i = 0; i < samples.length; i += sampleBlockSize) {
            const sampleChunk = samples.slice(i, i + sampleBlockSize);
            const mp3buf = mp3encoder.encodeBuffer(sampleChunk);
            if (mp3buf.length > 0) {
              mp3Data.push(mp3buf);
            }
          }
          
          // 完成编码
          const end = mp3encoder.flush();
          if (end.length > 0) {
            mp3Data.push(end);
          }
          
          // 合并所有数据块
          const blob = new Blob(mp3Data, { type: 'audio/mp3' });
          resolve(blob);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = (error) => {
        reject(error);
      };
      
      reader.readAsArrayBuffer(file);
    } catch (error) {
      reject(error);
    }
  });
};

// 将 AudioBuffer 转换为 WAV 格式
const convertToWav = (audioBuffer) => {
  const numOfChan = audioBuffer.numberOfChannels;
  const length = audioBuffer.length * numOfChan * 2;
  const buffer = new ArrayBuffer(44 + length);
  const view = new DataView(buffer);
  const channels = [];
  let offset = 0;
  let pos = 0;

  // 写入 WAV 文件头
  writeUTFBytes(view, 0, 'RIFF');
  view.setUint32(4, 36 + length, true);
  writeUTFBytes(view, 8, 'WAVE');
  writeUTFBytes(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numOfChan, true);
  view.setUint32(24, audioBuffer.sampleRate, true);
  view.setUint32(28, audioBuffer.sampleRate * 2 * numOfChan, true);
  view.setUint16(32, numOfChan * 2, true);
  view.setUint16(34, 16, true);
  writeUTFBytes(view, 36, 'data');
  view.setUint32(40, length, true);

  // 写入音频数据
  for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
    channels.push(audioBuffer.getChannelData(i));
  }

  while (pos < audioBuffer.length) {
    for (let i = 0; i < numOfChan; i++) {
      const sample = Math.max(-1, Math.min(1, channels[i][pos]));
      view.setInt16(44 + offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
      offset += 2;
    }
    pos++;
  }

  return new Blob([buffer], { type: 'audio/wav' });
};

// 辅助函数：写入 UTF 字节
const writeUTFBytes = (view, offset, string) => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};

export { digitalHumanService, fileUploadService }; 