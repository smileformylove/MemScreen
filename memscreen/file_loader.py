"""
Enhanced File Loader with Intelligent Encoding Detection

This module provides robust file loading capabilities with automatic encoding detection,
handling various text encodings including UTF-8, GBK, GB2312, Big5, and more.
"""

import os
from typing import Optional, Tuple, List, Dict
from pathlib import Path


class FileLoader:
    """Intelligent file loader with encoding detection."""

    # Common encodings to try (in order of preference)
    ENCODINGS = [
        'utf-8-sig',  # UTF-8 with BOM
        'utf-8',
        'gbk',        # Chinese Simplified
        'gb2312',     # Chinese Simplified (older)
        'gb18030',    # Chinese Simplified (comprehensive)
        'big5',       # Chinese Traditional
        'big5hkscs',  # Hong Kong
        'shift_jis',  # Japanese
        'euc-jp',     # Japanese
        'euc-kr',     # Korean
        'latin-1',    # Fallback (will never fail)
    ]

    @staticmethod
    def count_valid_characters(content: str) -> Dict[str, int]:
        """
        Count valid characters in content by category.

        Returns dict with counts for different character categories.
        """
        if not content:
            return {'total': 0, 'printable': 0, 'chinese': 0, 'japanese': 0, 'korean': 0, 'replacement': 0}

        stats = {
            'total': len(content),
            'printable': 0,
            'chinese': 0,
            'japanese': 0,
            'korean': 0,
            'replacement': 0,
        }

        for char in content:
            # Check for replacement character
            if char == '\ufffd':
                stats['replacement'] += 1
                continue

            # Count printable ASCII
            if char.isprintable():
                stats['printable'] += 1

            # Count Chinese characters (CJK Unified Ideographs)
            if '\u4e00' <= char <= '\u9fff':
                stats['chinese'] += 1

            # Count Japanese-specific characters (Hiragana and Katakana)
            elif '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff':
                stats['japanese'] += 1

            # Count Korean characters (Hangul)
            elif '\uac00' <= char <= '\ud7af' or '\u1100' <= char <= '\u11ff':
                stats['korean'] += 1

        return stats

    @staticmethod
    def detect_language(content: str) -> Optional[str]:
        """
        Detect the primary language of the content.

        Returns: 'zh-CN', 'zh-TW', 'ja', 'ko', or None
        """
        stats = FileLoader.count_valid_characters(content)

        # Count CJK characters
        cjk_total = stats['chinese'] + stats['japanese'] + stats['korean']
        if cjk_total == 0:
            return None

        # Detect Japanese (has Kana characters)
        if stats['japanese'] > 0:
            return 'ja'

        # Detect Korean (has Hangul characters)
        if stats['korean'] > 0:
            return 'ko'

        # For Chinese, we can't easily distinguish Simplified vs Traditional
        # without a dictionary, so return generic Chinese
        if stats['chinese'] > 0:
            return 'zh'

        return None

    @staticmethod
    def validate_content(content: str, encoding: str) -> Tuple[bool, float]:
        """
        Validate if decoded content is reasonable for the given encoding.

        Returns:
            Tuple of (is_valid, confidence_score)
        """
        if not content:
            return True, 1.0

        stats = FileLoader.count_valid_characters(content)

        # Check for excessive replacement characters
        replacement_ratio = stats['replacement'] / stats['total'] if stats['total'] > 0 else 0
        if replacement_ratio > 0.05:  # More than 5% replacement chars
            return False, 0.0

        # Detect language
        detected_lang = FileLoader.detect_language(content)

        # Score based on encoding-language match
        encoding_lang_map = {
            'gbk': 'zh',
            'gb2312': 'zh',
            'gb18030': 'zh',
            'big5': 'zh',
            'big5hkscs': 'zh',
            'shift_jis': 'ja',
            'euc-jp': 'ja',
            'euc-kr': 'ko',
        }

        expected_lang = encoding_lang_map.get(encoding)

        # Calculate base score
        printable_ratio = stats['printable'] / stats['total'] if stats['total'] > 0 else 0
        cjk_ratio = (stats['chinese'] + stats['japanese'] + stats['korean']) / stats['total'] if stats['total'] > 0 else 0
        base_score = max(printable_ratio, cjk_ratio)

        # Apply language match bonus
        if expected_lang and detected_lang:
            if expected_lang == detected_lang:
                # Language matches - boost score
                score = min(1.0, base_score * 1.5)
            elif detected_lang == 'zh' and expected_lang == 'zh':
                # Both Chinese - can't distinguish, give neutral score
                score = base_score
            else:
                # Language mismatch - penalize
                score = base_score * 0.5
        else:
            # No clear language detection
            score = base_score

        # Content is valid if score is reasonable
        is_valid = score > 0.3

        return is_valid, score

    @staticmethod
    def detect_encoding(file_path: str) -> Optional[str]:
        """
        Detect file encoding using charset-normalizer or chardet library.

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding name or None
        """
        # Try charset-normalizer first (more accurate)
        try:
            from charset_normalizer import from_path
            result = from_path(file_path)
            if result:
                best_match = result.best()
                if best_match:
                    encoding = best_match.encoding

                    # charset-normalizer uses different encoding names
                    # Map to Python's encoding names
                    encoding_map = {
                        'utf_8': 'utf-8',
                        'utf_8_sig': 'utf-8-sig',
                        'gb18030': 'gb18030',
                        'big5': 'big5',
                        'shift_jis': 'shift_jis',
                        'euc_jp': 'euc-jp',
                        'euc_kr': 'euc-kr',
                        'cp932': 'shift_jis',  # Windows variant of shift_jis
                    }

                    normalized_encoding = encoding_map.get(encoding, encoding)

                    print(f"[FileLoader] Detected encoding (charset-normalizer): {normalized_encoding}")

                    return normalized_encoding
        except ImportError:
            print("[FileLoader] charset-normalizer not installed")
        except Exception as e:
            print(f"[FileLoader] charset-normalizer detection failed: {e}")

        # Fallback to chardet
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                encoding = result.get('encoding')
                confidence = result.get('confidence', 0)

                print(f"[FileLoader] Detected encoding (chardet): {encoding} (confidence: {confidence:.2f})")

                # Use detected encoding if confidence is reasonable
                # Lower threshold to 0.2 to catch more encodings
                if encoding and confidence > 0.2:
                    return encoding
        except ImportError:
            print("[FileLoader] chardet not installed, using fallback detection")
        except Exception as e:
            print(f"[FileLoader] chardet detection failed: {e}")

        return None

    @staticmethod
    def get_encoding_language(encoding: str) -> Optional[str]:
        """
        Get the language associated with an encoding.

        Returns: 'zh-CN', 'zh-TW', 'ja', 'ko', or None
        """
        lang_map = {
            # Simplified Chinese
            'gbk': 'zh-CN',
            'gb2312': 'zh-CN',
            'gb18030': 'zh-CN',
            # Traditional Chinese
            'big5': 'zh-TW',
            'big5hkscs': 'zh-TW',
            # Japanese
            'shift_jis': 'ja',
            'euc-jp': 'ja',
            'cp932': 'ja',
            # Korean
            'euc-kr': 'ko',
            # Western
            'latin-1': 'en',
            'windows-1252': 'en',
        }
        return lang_map.get(encoding)

    @classmethod
    def read_file(cls, file_path: str, encoding: Optional[str] = None) -> Tuple[str, str]:
        """
        Read file content with automatic encoding detection.

        Args:
            file_path: Path to the file
            encoding: Specific encoding to use (None for auto-detection)

        Returns:
            Tuple of (file_content, actual_encoding_used)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be decoded with any encoding
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Not a file: {file_path}")

        # If encoding specified, try it first
        if encoding:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                is_valid, score = cls.validate_content(content, encoding)
                if is_valid:
                    print(f"[FileLoader] Successfully read with specified encoding: {encoding} (score: {score:.2f})")
                    return content, encoding
                else:
                    print(f"[FileLoader] Content validation failed for encoding: {encoding} (score: {score:.2f})")
            except (UnicodeDecodeError, LookupError) as e:
                print(f"[FileLoader] Failed to read with encoding {encoding}: {e}")

        # Detect encoding with charset-normalizer/chardet
        detected_encoding = cls.detect_encoding(file_path)

        # Build prioritized encoding list
        encodings_to_try: List[str] = []

        # Priority 1: Detected encoding (from charset-normalizer/chardet)
        if detected_encoding:
            encodings_to_try.append(detected_encoding)

        # Priority 2: UTF-8 variants (most common)
        encodings_to_try.extend(['utf-8-sig', 'utf-8'])

        # Priority 3: Same-language encodings as detected
        if detected_encoding:
            lang_encoding_map = {
                'shift_jis': ['euc-jp'],  # Japanese
                'euc-jp': ['shift_jis'],
                'euc-kr': [],  # Korean (no other common Korean encodings)
                'gbk': ['gb2312', 'gb18030'],  # Simplified Chinese
                'gb2312': ['gbk', 'gb18030'],
                'gb18030': ['gbk', 'gb2312'],
                'big5': ['big5hkscs'],  # Traditional Chinese
                'big5hkscs': ['big5'],
            }

            if detected_encoding in lang_encoding_map:
                for enc in lang_encoding_map[detected_encoding]:
                    if enc and enc not in encodings_to_try:
                        encodings_to_try.append(enc)

        # Priority 4: All other standard encodings
        for enc in cls.ENCODINGS:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

        # Try all encodings and pick the best one
        best_content = None
        best_encoding = None
        best_score = -1

        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()

                # Validate and score content (with encoding context)
                is_valid, score = cls.validate_content(content, enc)

                # Print status
                if is_valid:
                    if score > best_score:
                        status = "✓ BETTER" if best_score >= 0 else "✓ VALID"
                    elif score == best_score:
                        status = "~ TIE"
                    else:
                        status = "✓ VALID"
                    print(f"[FileLoader] Encoding {enc}: {status} (score: {score:.2f})")
                else:
                    print(f"[FileLoader] Encoding {enc}: invalid (score: {score:.2f})")

                # Track best encoding
                if is_valid and score >= best_score:
                    # When scores are equal, use smart tie-breaking:
                    should_update = False

                    if score > best_score:
                        should_update = True
                    elif score == best_score:
                        if best_encoding is None:
                            should_update = True
                        else:
                            # Smart tie-breaking logic
                            enc_lang = cls.get_encoding_language(enc)
                            best_lang = cls.get_encoding_language(best_encoding)
                            detected_lang = cls.get_encoding_language(detected_encoding) if detected_encoding else None

                            # Helper function to check if two languages are in the same family
                            def same_language_family(lang1, lang2):
                                if not lang1 or not lang2:
                                    return False
                                # Same exact language
                                if lang1 == lang2:
                                    return True
                                # Both Chinese (simplified or traditional)
                                if lang1.startswith('zh') and lang2.startswith('zh'):
                                    return True
                                return False

                            # Rule 1: If current encoding is the detected encoding
                            if enc == detected_encoding:
                                # Only prefer detected encoding if it's clearly the right choice
                                # For same-language-family ties, prefer more common encodings (earlier in list)
                                if best_lang and same_language_family(enc_lang, best_lang):
                                    # Same language family - prefer the one that comes earlier in ENCODINGS list
                                    # But if current (detected) encoding is NOT in the list, don't prefer it
                                    if enc in cls.ENCODINGS and best_encoding in cls.ENCODINGS:
                                        # Both in list - keep the earlier one
                                        try:
                                            enc_idx = cls.ENCODINGS.index(enc)
                                            best_idx = cls.ENCODINGS.index(best_encoding)
                                            should_update = (enc_idx < best_idx)
                                        except ValueError:
                                            should_update = False
                                    elif best_encoding not in cls.ENCODINGS:
                                        # Current is in list but best isn't - prefer current
                                        should_update = True
                                    else:
                                        # Best is in list but current isn't - keep best
                                        should_update = False
                                else:
                                    # Different language families - prefer detected
                                    should_update = True

                            # Rule 2: For non-detected encodings
                            else:
                                # Important: If best is the detected encoding and language families differ, keep it
                                if best_encoding == detected_encoding and not same_language_family(enc_lang, best_lang):
                                    # Detected encoding should be preferred for different language families
                                    should_update = False
                                # If current encoding is in priority list
                                elif enc in cls.ENCODINGS:
                                    try:
                                        current_idx = cls.ENCODINGS.index(enc)
                                        # Only compare if best is also in list
                                        if best_encoding in cls.ENCODINGS:
                                            best_idx = cls.ENCODINGS.index(best_encoding)
                                            if current_idx < best_idx:
                                                should_update = True
                                        else:
                                            # Current in list, best not - prefer current
                                            should_update = True
                                    except ValueError:
                                        pass

                    if should_update:
                        best_content = content
                        best_encoding = enc
                        best_score = score

            except (UnicodeDecodeError, LookupError) as e:
                print(f"[FileLoader] Encoding {enc}: decode error - {type(e).__name__}")
                continue

        # Return best result
        if best_content is not None:
            print(f"[FileLoader] Successfully read with encoding: {best_encoding} (score: {best_score:.2f})")
            return best_content, best_encoding

        # Last resort: read as binary and decode with error handling
        print("[FileLoader] All encodings failed, using binary fallback")
        with open(file_path, 'rb') as f:
            raw_content = f.read()

        # Try UTF-8 with error replacement
        try:
            content = raw_content.decode('utf-8', errors='replace')
            print("[FileLoader] Decoded with UTF-8 (errors='replace')")
            return content, 'utf-8-fallback'
        except Exception as e:
            raise ValueError(f"Failed to decode file: {e}")

    @classmethod
    def read_file_clean(cls, file_path: str) -> str:
        """
        Read file and return clean content suitable for LLM processing.

        This method:
        1. Detects and uses the correct encoding
        2. Removes BOM markers
        3. Normalizes line endings
        4. Strips leading/trailing whitespace

        Args:
            file_path: Path to the file

        Returns:
            Clean file content as string
        """
        content, encoding = cls.read_file(file_path)

        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]

        # Normalize line endings to \n
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Strip leading/trailing empty lines
        content = content.strip()

        return content

    @staticmethod
    def get_filename(file_path: str) -> str:
        """
        Extract filename from path, handling both Unix and Windows paths.

        Args:
            file_path: Full file path

        Returns:
            Filename only
        """
        # Normalize path separators first
        # Windows paths use backslash, Unix uses forward slash
        normalized = file_path.replace('\\', '/')

        # Extract filename (everything after the last separator)
        # Handle both cases: with and without separator
        if '/' in normalized:
            return normalized.rsplit('/', 1)[-1]
        else:
            return normalized


def test_file_loader():
    """Test the file loader with various encodings."""
    import tempfile

    test_cases = [
        ('utf-8', '你好世界 Hello World 🌍'),
        ('gbk', '你好世界'),
        ('gb2312', '测试文件'),
        ('big5', '繁體中文'),
        ('utf-8-sig', '\ufeffUTF-8 with BOM'),
    ]

    print("=" * 60)
    print("Testing FileLoader")
    print("=" * 60)

    for encoding, test_content in test_cases:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', encoding=encoding,
                                            delete=False, suffix='.txt') as f:
                f.write(test_content)
                temp_path = f.name

            # Read with FileLoader
            loaded_content = FileLoader.read_file_clean(temp_path)

            # Check if content matches (allowing for BOM removal)
            expected = test_content.replace('\ufeff', '')
            success = loaded_content == expected

            status = "✓ PASS" if success else "✗ FAIL"
            print(f"\n{status} [{encoding}]")
            print(f"  Expected: {repr(expected)}")
            print(f"  Got:      {repr(loaded_content)}")

            # Clean up
            os.unlink(temp_path)

        except Exception as e:
            print(f"\n✗ ERROR [{encoding}]: {e}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_file_loader()
