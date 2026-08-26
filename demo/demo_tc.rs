//! 合併字型預覽：繁體中文、日本語、한국어與 Nerd Font 圖示。
const ICONS: [&str; 8] = ["󰄬", "", "", "󰘧", "", "", "", ""];

#[derive(Clone, Copy, Debug)]
enum Tone { Calm, Hint, Success }
impl Tone { fn label(self) -> &'static str {
    match self { Self::Calm => "寧靜", Self::Hint => "提示", Self::Success => "完成" }
} }
#[derive(Debug)]
struct Sample<'a> { label: &'a str, tone: Tone, icon: usize, bars: u8 }
trait Preview { fn line(&self) -> String; }
impl Preview for Sample<'_> {
    fn line(&self) -> String {
        let state = if self.bars >= 8 { "滿格" } else { "預覽" };
        let meter = "▰".repeat(self.bars as usize);
        format!("{} {:<2} {:<18} {:<2} {}",
            ICONS[self.icon], self.tone.label(), self.label, state, meter)
    }
}
macro_rules! s {
    ($label:literal, $tone:expr, $icon:expr, $bars:expr) =>
        { Sample { label: $label, tone: $tone, icon: $icon, bars: $bars } };
}
fn render<const N: usize>(rows: [Sample<'_>; N], title: &str) {
    println!("\n╭─ {title} ─╮");
    rows.iter()
        .filter(|r| r.bars > 0)
        .map(Preview::line)
        .for_each(|line| println!("│ {line}"));
    println!("╰─ 字形 / かな / 한글 / 圖示 ─╯");
}
fn main() { // 繁體中文註解 / 日本語コメント / 한국어 주석
    use Tone::*;
    let rows = [
        s!("繁體中文·字型", Success, 0, 8), s!("日本語·等幅テスト", Calm, 1, 6),
        s!("한국어·고정폭", Hint, 2, 7), s!("漢字／かな／한글", Success, 3, 9),
        s!("你好·東京·서울", Calm, 4, 5), s!("註解·字形·標點", Hint, 5, 8),
        s!("混排『你好』「ABC」", Success, 6, 10), s!("終端·準備·준비", Calm, 7, 4),
    ]; render(rows, "字型合併實驗室 · Font Lab");
}
