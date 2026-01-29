# Homebrew Formula for MemScreen
# To install: brew install MemScreen.rb

class Memscreen < Formula
  include Language::Python::Virtualenv

  desc "AI-Powered Visual Memory System - Ask Screen Anything"
  homepage "https://github.com/smileformylove/MemScreen"
  url "https://github.com/smileformylove/MemScreen.git",
    revision: "main"
  version "0.4.0"
  license "MIT"

  depends_on "python@3.13"
  depends_on "ollama"

  resource "setuptools" do
    url "https://files.pythonhosted.org/packages/source/s/setuptools/setuptools-75.8.0.tar.gz"
    sha256 "c5b845e95003a830e9e1eae79ca0a52c0b51e0b98caeda6b042e6fecf3a494b4"
  end

  def install
    venv = virtualenv_create(libexec, "python3.13")

    # Install Python dependencies
    venv.pip_install resources

    # Install MemScreen in editable mode
    system libexec/"bin/pip", "install", "-e", "."

    # Create wrapper scripts
    bin.install_symlink libexec/"bin/memscreen" => "memscreen"
    bin.install_symlink libexec/"bin/memscreen-chat" => "memscreen-chat"
    bin.install_symlink libexec/"bin/memscreen-screenshots" => "memscreen-screenshots"
    bin.install_symlink libexec/"bin/memscreen-process-mining" => "memscreen-process-mining"

    # Create macOS app launcher
    (buildpath/"MemScreen Launcher").write <<~EOS
      #!/bin/bash
      source #{libexec}/bin/activate
      exec python -m memscreen.memscreen "$@"
    EOS

    (buildpath/"MemScreen Chat Launcher").write <<~EOS
      #!/bin/bash
      source #{libexec}/bin/activate
      exec python -m memscreen.chat_ui "$@"
    EOS

    (buildpath/"MemScreen Screenshots Launcher").write <<~EOS
      #!/bin/bash
      source #{libexec}/bin/activate
      exec python -m memscreen.screenshot_ui "$@"
    EOS

    bin.install "MemScreen Launcher" => "memscreen-app"
    bin.install "MemScreen Chat Launcher" => "memscreen-chat-app"
    bin.install "MemScreen Screenshots Launcher" => "memscreen-screenshots-app"
  end

  def caveats
    <<~EOS
      MemScreen has been installed!

      To get started:
        1. Install Ollama (if not already installed):
           brew install ollama

        2. Pull the required AI models:
           ollama pull qwen3:1.7b
           ollama pull qwen2.5vl:3b
           ollama pull mxbai-embed-large:latest

        3. Start Ollama service:
           ollama serve

        4. Run MemScreen:
           memscreen

         Or launch specific components:
           memscreen-app              # Screen recorder
           memscreen-chat-app         # Chat interface
           memscreen-screenshots-app  # Screenshot browser

      For more information, visit:
        https://github.com/smileformylove/MemScreen
    EOS
  end

  test do
    system bin/"memscreen", "--help"
  end
end
