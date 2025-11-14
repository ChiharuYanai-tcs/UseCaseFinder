import sys
from orchestrator import UseCaseOrchestrator
from config import config  # この時点で既に.envが読み込まれている

def print_banner():
    """バナー表示"""
    banner = """
══════════════════════════════════════════════════════════════
                                                              
   ユースケース提案 AI エージェント                             
                                                              
   テクノロジーキーワードから革新的なユースケースを提案            
                                                              
══════════════════════════════════════════════════════════════
    """
    print(banner)

def main():
    """メイン関数"""
    # load_dotenv()の呼び出しは不要（config.pyで実行済み）
    
    # バナー表示
    print_banner()
    
    # APIキーチェック
    if not config.claude_api_key:
        print("エラー: ANTHROPIC_API_KEYが設定されていません")
        print(".envファイルにAPIキーを設定してください")
        return
    
    # オーケストレーター初期化
    orchestrator = UseCaseOrchestrator()
    
    # インタラクティブモード
    while True:
        try:
            print("\n" + "─" * 60)
            keyword = input("キーワードを入力してください (終了: quit/exit): ").strip()
            
            if keyword.lower() in ['quit', 'exit', 'q']:
                print("\n終了します")
                break
            
            if not keyword:
                print("キーワードを入力してください")
                continue
            
            # 処理実行
            result = orchestrator.process(keyword)
            
            # 結果表示
            print("\n" + "=" * 60)
            print("分析結果")
            print("=" * 60)
            print(result['analysis'])
            print("\n" + "=" * 60)
            
            # 継続確認
            cont = input("\n別のキーワードで検索しますか? (y/n): ").strip().lower()
            if cont != 'y':
                print("\n終了します")
                break
                
        except KeyboardInterrupt:
            print("\n\n終了します")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
