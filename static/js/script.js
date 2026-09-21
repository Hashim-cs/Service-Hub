document.addEventListener("DOMContentLoaded", function () {

    const images = [
        "/static/images/services/electrician.png",
        "/static/images/services/plumber.png",
        "/static/images/services/cleaning.jpg",
        "/static/images/services/beauty.jpg"
    ];

    let index = 0;
    const img = document.getElementById("heroImg");

    function changeImage() {
        index++;
        if (index >= images.length) {
            index = 0;
        }
        img.src = images[index];
    }

    setInterval(changeImage, 3000); // change every 3 seconds
});
// TESTIMONIAL SLIDER
const testimonials = document.querySelectorAll(".testimonial");
let tIndex = 0;

function nextTestimonial() {
    testimonials[tIndex].classList.remove("active");
    tIndex = (tIndex + 1) % testimonials.length;
    testimonials[tIndex].classList.add("active");
}

setInterval(nextTestimonial, 4000);

function openPopup() {
    document.getElementById("registerPopup").style.display = "block";
}

function closePopup() {
    document.getElementById("registerPopup").style.display = "none";
}
function openLoginPopup() {
    document.getElementById("loginPopup").style.display = "block";
}

function closeLoginPopup() {
    document.getElementById("loginPopup").style.display = "none";
}
