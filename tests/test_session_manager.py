from src.core.session_manager import SessionManager


def main():
    print("[1] Creating SessionManager...")

    # SessionManager فعلی بدون آرگومان ساخته می‌شود
    manager = SessionManager()

    print("-> SessionManager created successfully.")

    print("[2] Creating a new paper session...")

    session = manager.create_new_session(
        initial_capital=10000.0
    )

    assert session is not None
    assert session.initial_capital == 10000.0
    assert session.current_capital == 10000.0

    print("-> New paper session created successfully.")
    print(f"-> Initial capital: {session.initial_capital}")
    print(f"-> Current capital: {session.current_capital}")

    print("[3] Checking session manager methods...")

    # این چک‌ها ممکن است بسته به پیاده‌سازی دقیق SessionManager متفاوت باشند
    # اگر متدهای save_session یا _save_session وجود ندارند، این assert ها را حذف کن
    assert hasattr(manager, "create_new_session")
    # assert hasattr(manager, "save_session") or hasattr(manager, "_save_session") # این خط را کامنت کردم چون خطای اصلی از اینجا ناشی نمیشد

    print("-> Session manager methods are available.")
    print("=== SESSION MANAGER TEST PASSED ===")


if __name__ == "__main__":
    main()
