#!/bin/bash

# Terminal Tools - Bash, FileRead, TodoWrite
# 使用方法：source terminal_tools.sh

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# Bash - 执行命令并记录
# ============================================
function run_bash() {
    local cmd="$*"
    echo -e "${BLUE}[Bash]${NC} 执行命令: ${YELLOW}$cmd${NC}"
    echo "---"
    
    # 执行命令
    eval "$cmd"
    local exit_code=$?
    
    echo "---"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ 命令执行成功${NC}"
    else
        echo -e "${RED}✗ 命令执行失败 (退出码: $exit_code)${NC}"
    fi
    
    # 记录到日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Command: $cmd | Exit Code: $exit_code" >> ~/.terminal_tools_history.log
    
    return $exit_code
}

# ============================================
# FileRead - 读取文件内容
# ============================================
function file_read() {
    local file_path="$1"
    local start_line="${2:-1}"
    local end_line="${3:-}"
    
    if [ -z "$file_path" ]; then
        echo -e "${RED}错误: 请提供文件路径${NC}"
        echo "用法: file_read <文件路径> [起始行] [结束行]"
        return 1
    fi
    
    if [ ! -f "$file_path" ]; then
        echo -e "${RED}错误: 文件不存在: $file_path${NC}"
        return 1
    fi
    
    echo -e "${BLUE}[FileRead]${NC} 读取文件: ${YELLOW}$file_path${NC}"
    
    # 获取文件总行数
    local total_lines=$(wc -l < "$file_path")
    echo -e "文件总行数: ${GREEN}$total_lines${NC}"
    echo "---"
    
    # 读取文件内容
    if [ -z "$end_line" ]; then
        # 只指定起始行，读取到文件末尾
        sed -n "${start_line},\$p" "$file_path" | nl -ba -v "$start_line"
    else
        # 指定起始行和结束行
        sed -n "${start_line},${end_line}p" "$file_path" | nl -ba -v "$start_line"
    fi
    
    echo "---"
    echo -e "${GREEN}✓ 文件读取完成${NC}"
}

# ============================================
# TodoWrite - 写入待办事项
# ============================================
function todo_write() {
    local todo_file="${TODO_FILE:-$HOME/.terminal_todos.md}"
    local action="$1"
    shift
    
    case "$action" in
        add)
            local task="$*"
            if [ -z "$task" ]; then
                echo -e "${RED}错误: 请提供待办事项内容${NC}"
                echo "用法: todo_write add <待办事项>"
                return 1
            fi
            
            # 创建文件（如果不存在）
            if [ ! -f "$todo_file" ]; then
                echo "# Terminal Todos" > "$todo_file"
                echo "" >> "$todo_file"
                echo "创建日期: $(date '+%Y-%m-%d %H:%M:%S')" >> "$todo_file"
                echo "" >> "$todo_file"
            fi
            
            # 添加待办事项
            echo "- [ ] $task (添加于 $(date '+%Y-%m-%d %H:%M:%S'))" >> "$todo_file"
            echo -e "${GREEN}✓ 已添加待办事项:${NC} $task"
            echo -e "  保存位置: ${YELLOW}$todo_file${NC}"
            ;;
            
        done)
            local task_number="$1"
            if [ -z "$task_number" ]; then
                echo -e "${RED}错误: 请提供待办事项编号${NC}"
                echo "用法: todo_write done <编号>"
                return 1
            fi
            
            if [ ! -f "$todo_file" ]; then
                echo -e "${RED}错误: 待办事项文件不存在${NC}"
                return 1
            fi
            
            # 标记为完成
            sed -i.bak "${task_number}s/- \[ \]/- [x]/" "$todo_file"
            echo -e "${GREEN}✓ 已标记待办事项 #$task_number 为完成${NC}"
            ;;
            
        list)
            if [ ! -f "$todo_file" ]; then
                echo -e "${YELLOW}暂无待办事项${NC}"
                return 0
            fi
            
            echo -e "${BLUE}[TodoWrite]${NC} 待办事项列表:"
            echo "---"
            cat "$todo_file"
            echo "---"
            
            # 统计
            local total=$(grep -c "^- \[" "$todo_file" 2>/dev/null || echo 0)
            local done=$(grep -c "^- \[x\]" "$todo_file" 2>/dev/null || echo 0)
            local pending=$(grep -c "^- \[ \]" "$todo_file" 2>/dev/null || echo 0)
            
            echo -e "总计: ${BLUE}$total${NC} | 已完成: ${GREEN}$done${NC} | 待完成: ${YELLOW}$pending${NC}"
            ;;
            
        clear)
            if [ -f "$todo_file" ]; then
                rm "$todo_file"
                echo -e "${GREEN}✓ 已清空所有待办事项${NC}"
            else
                echo -e "${YELLOW}待办事项文件不存在${NC}"
            fi
            ;;
            
        *)
            echo -e "${YELLOW}TodoWrite 工具 - 待办事项管理${NC}"
            echo ""
            echo "用法:"
            echo "  todo_write add <待办事项>     - 添加新的待办事项"
            echo "  todo_write done <编号>        - 标记待办事项为完成"
            echo "  todo_write list               - 显示所有待办事项"
            echo "  todo_write clear              - 清空所有待办事项"
            echo ""
            echo "示例:"
            echo "  todo_write add 修复 VAD 合并问题"
            echo "  todo_write done 5"
            echo "  todo_write list"
            ;;
    esac
}

# ============================================
# 帮助信息
# ============================================
function terminal_tools_help() {
    echo -e "${GREEN}=== Terminal Tools ===${NC}"
    echo ""
    echo -e "${BLUE}1. Bash - 执行命令${NC}"
    echo "   run_bash <命令>"
    echo "   示例: run_bash ls -la"
    echo ""
    echo -e "${BLUE}2. FileRead - 读取文件${NC}"
    echo "   file_read <文件路径> [起始行] [结束行]"
    echo "   示例: file_read main.py"
    echo "   示例: file_read main.py 10 20"
    echo ""
    echo -e "${BLUE}3. TodoWrite - 待办事项${NC}"
    echo "   todo_write add <待办事项>    - 添加"
    echo "   todo_write done <编号>       - 完成"
    echo "   todo_write list              - 列表"
    echo "   todo_write clear             - 清空"
    echo ""
    echo -e "${YELLOW}提示: 输入 'tt' 可快速查看此帮助${NC}"
}

# 快捷别名
alias tt='terminal_tools_help'
alias bash_run='run_bash'
alias fread='file_read'
alias todo='todo_write'

# 显示欢迎信息
echo -e "${GREEN}✓ Terminal Tools 已加载${NC}"
echo -e "输入 ${YELLOW}tt${NC} 或 ${YELLOW}terminal_tools_help${NC} 查看帮助"
