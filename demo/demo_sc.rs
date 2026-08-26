//! 合并字体预览：简体中文、日本語、한국어与 Nerd Font 图标。
const ICONS: [&str; 8] = ["󰄬", "", "", "󰘧", "", "", "", ""];

#[derive(Clone, Copy, Debug)]
enum Tone { Calm, Hint, Success }
impl Tone { fn label(self) -> &'static str {
    match self { Self::Calm => "平静", Self::Hint => "提醒", Self::Success => "成功" }
} }
#[derive(Debug)]
struct Sample<'a> { label: &'a str, tone: Tone, icon: usize, bars: u8 }
trait Preview { fn line(&self) -> String; }
impl Preview for Sample<'_> {
    fn line(&self) -> String {
        let state = if self.bars >= 8 { "满格" } else { "预览" };
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
    println!("╰─ 字形 / かな / 한글 / 图标 ─╯");
}
fn main() { // 简体中文注释 / 日本語コメント / 한국어 주석
    use Tone::*;
    let rows = [
        s!("简体中文·字体", Success, 0, 8), s!("日本語·等幅テスト", Calm, 1, 6),
        s!("한국어·고정폭", Hint, 2, 7), s!("汉字／かな／한글", Success, 3, 9),
        s!("你好·東京·서울", Calm, 4, 5), s!("注释·字形·标点", Hint, 5, 8),
        s!("混排『你好』「ABC」", Success, 6, 10), s!("终端·準備·준비", Calm, 7, 4),
    ]; render(rows, "字体合并实验室 · Font Lab");
}
